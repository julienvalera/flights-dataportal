# transformation

Transformations dbt pour le domaine flights, exécutées sur AWS Athena avec stockage Iceberg sur S3.

## Stack

- **dbt-core** + **dbt-athena-community**
- Source : table Iceberg `flights_db.flights` (AWS Glue / Athena)
- Sortie : tables Iceberg dans `flights_db` sur S3 (`s3://cfm-datalake-iceberg/dbt/`)

## Modèles

| Modèle | Couche | Description |
|---|---|---|
| `avg_delay_by_carrier` | mart | Retards moyens au départ et à l'arrivée par compagnie aérienne |

## Configuration de la connexion

La connexion Athena est définie dans `profiles.yml` via des variables d'environnement :

| Variable | Défaut | Description |
|---|---|---|
| `AWS_REGION` | `eu-west-1` | Région AWS |
| `ATHENA_STAGING_DIR` | `s3://cfm-datalake-iceberg/athena-results/` | Bucket de résultats Athena |
| `ATHENA_DATA_DIR` | `s3://cfm-datalake-iceberg/dbt/` | Bucket de stockage des tables dbt |

Les credentials AWS sont lus depuis l'environnement standard (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` ou profil IAM).

## Commandes

```shell
# Installer les dépendances
uv sync

# Installer les packages dbt
uv run dbt deps

# Exécuter tous les modèles
uv run dbt run --profiles-dir .

# Exécuter un modèle spécifique
uv run dbt run --profiles-dir . --select avg_delay_by_carrier

# Lancer les tests
uv run dbt test --profiles-dir .

# Générer et servir la documentation
uv run dbt docs generate --profiles-dir .
uv run dbt docs serve --profiles-dir .
```

> `--profiles-dir .` est requis car `profiles.yml` est dans ce dossier plutôt que dans `~/.dbt/`.