# flights-dataportal

PoC de standardisation d'accès aux données du domaine via un SDK Python.

Les données de vols NYC 2013 sont stockées dans une table Apache Iceberg sur AWS S3/Glue, décrites par un contrat ODCS, publiées dans OpenMetadata, et exposées via un SDK Python.

## Structure du repo

| Dossier | Rôle |
|---|---|
| [`odcs-contracts/`](odcs-contracts/) | Contrats de données ODCS (YAML uniquement) |
| [`infra/`](infra/) | Infrastructure AWS via Terraform (S3, Glue) |
| [`ingestion/`](ingestion/) | Chargement de `flights.csv` dans Iceberg/S3 |
| [`catalog-sync/`](catalog-sync/) | Synchronisation des contrats vers OpenMetadata |
| [`sdk/`](sdk/) | SDK Python pour consommer les data products |
| [`scripts/`](scripts/) | Scripts utilitaires (démarrage OpenMetadata, etc.) |

## Prérequis

- Python 3.13+, [uv](https://github.com/astral-sh/uv)
- AWS CLI configuré (accès S3 + Glue)
- [Terraform](https://www.terraform.io/) >= 1.0
- Docker (pour OpenMetadata local)

## Démarrage rapide

```shell
# 1. Déployer l'infra AWS
cd infra && terraform apply

# 2. Charger les données
cd ingestion && uv run python load_flights.py

# 3. Lancer OpenMetadata en local
./scripts/openmetadata.sh

# 4. Publier le data product dans OpenMetadata
cd catalog-sync && uv run python publish_to_openmetadata.py

# 5. Consommer via le SDK
cd sdk && uv run python main.py
```

## Stack technique

| Couche | Techno |
|---|---|
| Compute | AWS Athena |
| Stockage | AWS S3 (Apache Iceberg) |
| Catalogue données | AWS Glue + OpenMetadata 1.12.1 |
| Contrats de données | ODCS v3.1.0, datacontract-cli |
| SDK Python | pyiceberg[glue], boto3, polars |
| Infra | Terraform ~> 5.0 (provider AWS) |
| Package manager | uv (Python 3.13) |
