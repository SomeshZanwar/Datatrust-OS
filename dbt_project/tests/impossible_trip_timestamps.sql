select *
from {{ ref('stg_yellow_trips') }}
where dropoff_datetime < pickup_datetime