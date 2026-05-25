{{ config(schema='marts', materialized='table') }}
with incidents as (

    select *
    from governance.governance_incidents

),

final as (

    select
        incident_id,
        incident_key,
        asset_name,
        incident_type,
        severity,
        test_name,
        failure_count,
        violation_detail,
        status,
        detected_at,
        last_seen_at,
        resolved_at,

        case
            when status = 'RESOLVED'
                then extract(epoch from (resolved_at - detected_at)) / 3600
            else extract(epoch from (now() - detected_at)) / 3600
        end as incident_age_hours,

        case
            when status = 'RESOLVED' then true
            else false
        end as is_resolved,

        case
            when severity = 'CRITICAL' then 1
            when severity = 'HIGH' then 2
            when severity = 'MEDIUM' then 3
            when severity = 'LOW' then 4
            else 5
        end as severity_rank

    from incidents

)

select *
from final