select *
from {{ ref('stg_yellow_trips') }}
where fare_amount < 0