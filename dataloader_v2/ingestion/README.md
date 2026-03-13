# ingestion/

Charge `flights.csv` dans une table Apache Iceberg sur AWS S3/Glue.

Ce script est à exécuter **une seule fois** (ou pour re-seeder les données). Il crée la table Glue si elle n'existe pas et insère les données en mode append.

## Prérequis

- AWS CLI configuré avec les droits S3 + Glue
- Infrastructure déployée (voir [`infra/`](../infra/))
- Variables d'environnement : `S3_BUCKET`, `AWS_REGION`, `GLUE_DATABASE`, `TABLE_NAME`

## Lancer

```shell
cd ingestion
uv run python load_flights.py
```

## Dépendances

- `pandas`, `pyarrow` — lecture du CSV
- `pyiceberg[glue]` — écriture Iceberg + catalogue Glue
- `boto3` — AWS SDK
