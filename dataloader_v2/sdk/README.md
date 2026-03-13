# sdk/

SDK Python pour abstraire la consommation des data products. À terme, ce package sera publié sur un repository PyPI privé et utilisable directement par les Data Scientists.

## Usage

```python
import dataloader

# Récupère les 5 premières lignes du data product "flights"
df = dataloader.get("flights")
```

## Lancer la démo

```shell
cd sdk
uv run python main.py
```

## API

### `dataloader.get(dataset_id: str) -> polars.DataFrame`

Résout le `dataset_id` via AWS Glue, localise la table Iceberg correspondante sur S3, et retourne un DataFrame Polars (limite 5 lignes par défaut).

**Prérequis** : AWS CLI configuré avec les droits Glue + S3.

## Dépendances

- `pyiceberg[glue]` — lecture des tables Iceberg via catalogue Glue
- `boto3` — résolution des métadonnées Glue
- `polars` — DataFrame de retour
- `matplotlib` — visualisations exploratoires

## Roadmap

- [ ] Paramétrer la limite de lignes
- [ ] Support multi-environnement (dev/prod)
- [ ] Publication sur PyPI privé
- [ ] Typage complet et docstrings
