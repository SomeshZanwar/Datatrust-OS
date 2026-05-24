select *
from {{ ref('stg_yellow_trips') }}
where pickup_datetime < '2023-01-01'
   or pickup_datetime >= '2023-02-01'