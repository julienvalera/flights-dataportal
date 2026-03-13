import boto3
import json
import polars as pl

def get(dataset_id: str):
    glue = boto3.client("glue")
    resp = glue.get_table(
        DatabaseName="flights_db",
        Name=dataset_id,
    )
    table = resp["Table"]
    location = table["Parameters"]["metadata_location"]
    query = pl.scan_iceberg(location).limit(5)
    df = query.collect()
