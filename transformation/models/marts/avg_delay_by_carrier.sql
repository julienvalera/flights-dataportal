{{
    config(
        materialized='table',
        table_type='iceberg',
        format='parquet',
        s3_data_dir=var('s3_data_dir', 's3://cfm-datalake-iceberg/dbt/'),
    )
}}

select
    carrier,
    name,
    count(*)                                as total_flights,
    count_if(dep_delay is not null)         as non_cancelled_flights,
    round(avg(dep_delay), 2)                as avg_dep_delay_minutes,
    round(avg(arr_delay), 2)                as avg_arr_delay_minutes
from {{ source('flights_db', 'flights') }}
group by carrier, name
order by avg_dep_delay_minutes desc
