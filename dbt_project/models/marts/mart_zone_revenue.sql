{{ config(schema='marts', materialized='table') }}

with trips as (

    select *
    from {{ ref('stg_yellow_trips') }}

),

trust as (

    select
        asset_name,
        composite_trust_score,
        trust_label
    from governance.latest_trust_scores
    where asset_name = 'stg_yellow_trips'

),

open_incidents as (

    select
        asset_name,
        count(*) as open_incident_count,
        min(
            case
                when severity = 'CRITICAL' then 1
                when severity = 'HIGH' then 2
                when severity = 'MEDIUM' then 3
                when severity = 'LOW' then 4
                else 5
            end
        ) as highest_severity_rank
    from governance.governance_incidents
    where status = 'OPEN'
      and asset_name = 'stg_yellow_trips'
    group by asset_name

),

governance_context as (

    select
        trust.asset_name,
        trust.composite_trust_score as trust_score,
        trust.trust_label,
        coalesce(open_incidents.open_incident_count, 0) as open_incident_count,
        case open_incidents.highest_severity_rank
            when 1 then 'CRITICAL'
            when 2 then 'HIGH'
            when 3 then 'MEDIUM'
            when 4 then 'LOW'
            else 'NONE'
        end as highest_open_severity
    from trust
    left join open_incidents
        on trust.asset_name = open_incidents.asset_name

),

zone_revenue as (

    select
        pickup_date,
        pickup_location_id,
        count(*) as trip_count,
        sum(total_amount) as total_revenue,
        avg(fare_amount) as avg_fare,
        avg(trip_distance) as avg_trip_distance
    from trips
    group by
        pickup_date,
        pickup_location_id

),

final as (

    select
        zone_revenue.pickup_date,
        zone_revenue.pickup_location_id,

        -- Zone lookup will be added after we load the TLC zone seed.
        null::text as zone_name,
        null::text as borough,

        zone_revenue.trip_count,
        zone_revenue.total_revenue,
        zone_revenue.avg_fare,
        zone_revenue.avg_trip_distance,

        governance_context.trust_score,
        governance_context.trust_label,
        governance_context.open_incident_count,
        governance_context.highest_open_severity,

        {{ data_reliability_status(
            'governance_context.trust_score',
            'governance_context.open_incident_count',
            'governance_context.highest_open_severity'
        ) }} as data_reliability_status

    from zone_revenue
    cross join governance_context

)

select *
from final