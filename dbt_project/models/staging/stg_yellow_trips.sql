{{ config(schema='staging', materialized='view') }}
with source as (

    select *
    from {{ source('raw', 'yellow_trips') }}

),

renamed as (

    select
        md5(
            concat_ws(
                '||',
                "VendorID"::text,
                tpep_pickup_datetime::text,
                tpep_dropoff_datetime::text,
                "PULocationID"::text,
                "DOLocationID"::text,
                fare_amount::text,
                total_amount::text,
                _source_file::text
            )
        ) as trip_id,

        'yellow' as source_system,

        "VendorID"::integer as vendor_id,
        tpep_pickup_datetime::timestamp as pickup_datetime,
        tpep_dropoff_datetime::timestamp as dropoff_datetime,
        date(tpep_pickup_datetime) as pickup_date,

        "PULocationID"::integer as pickup_location_id,
        "DOLocationID"::integer as dropoff_location_id,

        passenger_count::numeric as passenger_count,
        trip_distance::numeric as trip_distance,
        fare_amount::numeric as fare_amount,
        tip_amount::numeric as tip_amount,
        total_amount::numeric as total_amount,

        payment_type::integer as payment_type,
        "RatecodeID"::integer as ratecode_id,
        store_and_fwd_flag::text as store_and_fwd_flag,

        _source_file as source_file,
        _source_file_hash as source_file_hash,
        _ingested_at as ingested_at

    from source

)

select *
from renamed