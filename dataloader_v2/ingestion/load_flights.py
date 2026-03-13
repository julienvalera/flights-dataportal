"""
Loader PoC : flights.csv → Apache Iceberg sur AWS S3 (via Glue Catalog)

Prérequis AWS :
  - Un bucket S3 (ex: my-datalake-bucket)
  - Un database Glue existant ou à créer (ex: flights_db)
  - Credentials AWS configurés (env vars, ~/.aws/credentials ou IAM role)

Dépendances :
  pip install pyiceberg[glue] pyarrow
"""

import os
import pyarrow as pa
import pyarrow.csv as pa_csv
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError, NoSuchTableError

# ---------------------------------------------------------------------------
# Configuration – à adapter ou passer via variables d'environnement
# ---------------------------------------------------------------------------
S3_BUCKET = os.getenv("S3_BUCKET", "cfm-datalake-iceberg")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
GLUE_DATABASE = os.getenv("GLUE_DATABASE", "flights_db")
TABLE_NAME = "flights"
CSV_PATH = os.getenv("CSV_PATH", "flights.csv")

ICEBERG_LOCATION = f"s3://{S3_BUCKET}/iceberg/{TABLE_NAME}"


def load_csv(path: str) -> pa.Table:
    """Lit le CSV et retourne un PyArrow Table avec les bons types."""
    table = pa_csv.read_csv(
        path,
    )
    return table


def _iceberg_schema():
    """Schéma Iceberg hardcodé pour flights.csv."""
    from pyiceberg.schema import Schema
    from pyiceberg.types import (
        NestedField, LongType, DoubleType, StringType, TimestampType,
    )

    return Schema(
        NestedField(field_id=1, name="id", field_type=LongType(), required=False),
        NestedField(field_id=2, name="year", field_type=LongType(), required=False),
        NestedField(field_id=3, name="month", field_type=LongType(), required=False),
        NestedField(field_id=4, name="day", field_type=LongType(), required=False),
        NestedField(field_id=5, name="dep_time", field_type=DoubleType(), required=False),
        NestedField(field_id=6, name="sched_dep_time", field_type=LongType(), required=False),
        NestedField(field_id=7, name="dep_delay", field_type=DoubleType(), required=False),
        NestedField(field_id=8, name="arr_time", field_type=DoubleType(), required=False),
        NestedField(field_id=9, name="sched_arr_time", field_type=LongType(), required=False),
        NestedField(field_id=10, name="arr_delay", field_type=DoubleType(), required=False),
        NestedField(field_id=11, name="carrier", field_type=StringType(), required=False),
        NestedField(field_id=12, name="flight", field_type=LongType(), required=False),
        NestedField(field_id=13, name="tailnum", field_type=StringType(), required=False),
        NestedField(field_id=14, name="origin", field_type=StringType(), required=False),
        NestedField(field_id=15, name="dest", field_type=StringType(), required=False),
        NestedField(field_id=16, name="air_time", field_type=DoubleType(), required=False),
        NestedField(field_id=17, name="distance", field_type=LongType(), required=False),
        NestedField(field_id=18, name="hour", field_type=LongType(), required=False),
        NestedField(field_id=19, name="minute", field_type=LongType(), required=False),
        NestedField(field_id=20, name="time_hour", field_type=TimestampType(), required=False),
        NestedField(field_id=21, name="name", field_type=StringType(), required=False),
    )


def _partition_spec():
    """Partitionnement Iceberg : year / month."""
    from pyiceberg.partitioning import PartitionSpec, PartitionField
    from pyiceberg.transforms import IdentityTransform

    return PartitionSpec(
        PartitionField(source_id=2, field_id=1000, transform=IdentityTransform(), name="year"),
        PartitionField(source_id=3, field_id=1001, transform=IdentityTransform(), name="month"),
    )


def get_or_create_table(catalog, arrow_table: pa.Table):
    """Crée la table Iceberg si elle n'existe pas, sinon la récupère."""
    full_table_name = f"{GLUE_DATABASE}.{TABLE_NAME}"

    # Créer le namespace (database Glue) si nécessaire
    try:
        catalog.create_namespace(GLUE_DATABASE)
        print(f"Namespace '{GLUE_DATABASE}' créé.")
    except NamespaceAlreadyExistsError:
        pass

    # Créer ou récupérer la table
    try:
        table = catalog.load_table(full_table_name)
        print(f"Table '{full_table_name}' existante chargée.")
    except NoSuchTableError:
        table = catalog.create_table(
            identifier=full_table_name,
            schema=_iceberg_schema(),
            location=ICEBERG_LOCATION,
            partition_spec=_partition_spec(),
        )
        print(f"Table '{full_table_name}' créée à {ICEBERG_LOCATION}.")

    return table


def main():
    print(f"Chargement de {CSV_PATH}...")
    arrow_table = load_csv(CSV_PATH)
    print(f"  {len(arrow_table)} lignes, {len(arrow_table.schema)} colonnes.")

    # Connexion au Glue Catalog
    catalog = load_catalog(
        "glue",
        **{
            "type": "glue",
            "s3.region": AWS_REGION,
        },
    )

    table = get_or_create_table(catalog, arrow_table)

    print("Écriture dans Iceberg (append)...")
    table.append(arrow_table)
    print("Chargement terminé.")

    # Vérification rapide via scan Iceberg
    result = table.scan(limit=3).to_arrow()
    print(f"\nAperçu des 3 premières lignes :\n{result}")


if __name__ == "__main__":
    main()
