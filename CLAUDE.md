# CLAUDE.md — flights-dataportal

## A ne JAMAIS lire
- `docker-volume/` — volume Docker monté, ignoré dans git
- `docker-compose.yml` — généré par `scripts/openmetadata.sh`, ignoré dans git

## Références rapides
- OpenMetadata : http://localhost:8585, credentials admin@open-metadata.org / admin
- Version OM serveur : 1.12.1

## Vue d'ensemble

PoC de standardisation d'accès aux données du domaine via un SDK Python.
- **Données sources** : `flights.csv` → table Iceberg dans AWS Glue (format Iceberg, stockage S3)
- **Standard de contrat** : ODCS v3.1.0 (spec `flights.yaml`)
- **SDK** : `dataloader.py` — à terme publié comme lib Python
- **Catalogue de métadonnées** : OpenMetadata (lancé en local via Docker Compose)

## Stack technique

| Couche | Techno |
|---|---|
| Compute | AWS Athena |
| Stockage | AWS S3 (Iceberg) |
| Catalogue données | AWS Glue + OpenMetadata |
| SDK Python | pyiceberg[glue], boto3, polars |
| Transformations | dbt-core + dbt-athena-community |
| Infra | Terraform |
| Package manager | uv (Python 3.13) |
| Contrats de données | datacontract-cli, ODCS v3.1.0 |

## Arborescence

```
cfm-dataportal/
├── scripts/
│   └── openmetadata.sh         # Télécharge docker-compose.yml + lance OM en local
├── odcs-contracts/                    # Contrats de données (YAML uniquement)
│   └── flights.yaml               # Spec ODCS : schémas, qualité, SLA, owners
├── infra/                      # Terraform : S3 + Glue database
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── ingestion/                  # Chargement CSV → Iceberg/S3
│   ├── pyproject.toml
│   ├── load_flights.py         # Crée table Glue + charge flights.csv
│   └── flights.csv             # Données sources (seed)
├── catalog-sync/               # Synchronisation contrats → OpenMetadata
│   ├── pyproject.toml
│   ├── load-env.sh             # Export des vars pour datacontract-cli → Athena
│   └── publish_to_openmetadata.py  # Publie le data product dans OM via REST API
├── transformation/             # Transformations dbt (Athena + Iceberg)
│   ├── pyproject.toml          # dbt-core + dbt-athena-community
│   ├── dbt_project.yml         # Config dbt (profil: cfm_flights)
│   ├── profiles.yml            # Connexion Athena (variables d'env AWS)
│   └── models/
│       ├── sources/
│       │   └── flights_source.yml          # Source: awsdatacatalog.flights_db.flights
│       └── marts/
│           ├── avg_delay_by_carrier.sql    # Retards moyens par compagnie (table Iceberg)
│           └── avg_delay_by_carrier.yml    # Tests + documentation
└── sdk/                        # SDK Python (futur package PyPI)
    ├── pyproject.toml
    ├── dataloader.py           # SDK Python (fichier principal)
    └── main.py                 # Script de démo / simulation du SDK
```

## Fichiers clés par tâche

| Je travaille sur... | Lire en priorité |
|---|---|
| Le SDK / l'API consommateur | `sdk/dataloader.py` |
| L'ingestion des données | `ingestion/load_flights.py` |
| Le contrat de données | `odcs-contracts/flights.yaml` |
| L'infra AWS | `infra/main.tf`, `infra/variables.tf` |
| OpenMetadata local | voir Références rapides |
| Publier dans OpenMetadata | `catalog-sync/publish_to_openmetadata.py`, `odcs-contracts/flights.yaml` |
| Les transformations dbt | `transformation/models/marts/avg_delay_by_carrier.sql`, `transformation/profiles.yml` |

## Conventions d'implémentation
- OpenMetadata : utiliser `requests` directement (pas `openmetadata-ingestion` SDK)
- Pas de type hints sur les scripts utilitaires (hors dataloader.py)

## Commandes utiles

```shell
# OpenMetadata — démarrage (télécharge docker-compose.yml si absent)
./scripts/openmetadata.sh

# Logs
docker compose logs -f openmetadata_ingestion

# Contrats de données (depuis catalog-sync/, après avoir sourcé load-env.sh)
cd catalog-sync
source load-env.sh
uv run datacontract lint ../odcs-contracts/flights.yaml
uv run datacontract test ../odcs-contracts/flights.yaml
uv run datacontract export --format html --output datacontract.html ../odcs-contracts/flights.yaml

# Synchronisation vers OpenMetadata (depuis catalog-sync/)
cd catalog-sync
uv run python publish_to_openmetadata.py

# Ingestion (depuis ingestion/)
cd ingestion
uv run python load_flights.py

# SDK (depuis sdk/)
cd sdk
uv run python main.py

# Transformations dbt (depuis transformation/)
cd transformation
uv sync
uv run dbt deps
uv run dbt run --profiles-dir . --select avg_delay_by_carrier
uv run dbt test --profiles-dir . --select avg_delay_by_carrier

# Terraform (depuis infra/)
cd infra
terraform init
terraform plan
terraform apply
```
