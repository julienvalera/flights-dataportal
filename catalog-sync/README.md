# catalog-sync/

Synchronise les contrats de données ([`odcs-contracts/`](../odcs-contracts/)) vers OpenMetadata, et valide les contrats via `datacontract-cli` contre les données réelles sur Athena.

## Prérequis

- OpenMetadata démarré en local : `docker compose up -d` (voir racine)
- Accès à l'URL http://localhost:8585
- Variables AWS pour `datacontract-cli` (voir `load-env.sh`)

## Publier le data product dans OpenMetadata

```shell
cd catalog-sync
uv run python publish_to_openmetadata.py
```

Résultat : http://localhost:8585/dataProduct/data-engineering.flights

## Valider le contrat (datacontract-cli)

Copier `.env.example` en `.env` et renseigner les credentials AWS, puis :

```shell
cd catalog-sync
source load-env.sh
uv run datacontract lint ../odcs-contracts/flights.yaml
uv run datacontract test ../odcs-contracts/flights.yaml
uv run datacontract export --format html --output datacontract.html ../odcs-contracts/flights.yaml
```

> `.env` et `datacontract.html` sont dans le `.gitignore` — ne jamais les commiter.

## Dépendances

- `pyyaml` — lecture des contrats ODCS
- `requests` — appels REST vers l'API OpenMetadata
- `datacontract-cli` — lint, test et export des contrats
