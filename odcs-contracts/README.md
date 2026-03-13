# odcs-contracts/

Contrats de données au format [ODCS v3.1.0](https://github.com/bitol-io/open-data-contract-standard).

Ce dossier contient **uniquement des fichiers YAML**. Il est la source de vérité pour les schémas, règles de qualité, SLA et propriétaires des data products.

## Fichiers

| Fichier | Data product |
|---|---|
| [`flights.yaml`](flights.yaml) | `flights` — vols NYC 2013 (JFK, LGA, EWR) |

## Valider et tester le contrat

Depuis [`catalog-sync/`](../catalog-sync/) après avoir configuré les variables AWS :

```shell
cd ../catalog-sync
source load-env.sh
uv run datacontract lint ../odcs-contracts/flights.yaml
uv run datacontract test ../odcs-contracts/flights.yaml
```
