"""
Publie le data product "flights" dans OpenMetadata à partir de odcs.yaml.

Prérequis : OpenMetadata démarré sur http://localhost:8585

Lancer depuis catalog-sync/ :
    uv run python publish_to_openmetadata.py
"""

import sys
import yaml
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ODCS_PATH = Path(__file__).parent.parent / "catalog" / "odcs.yaml"
OM_BASE = "http://localhost:8585/api/v1"
OM_EMAIL = "admin@open-metadata.org"
OM_PASSWORD = "admin"

# Mapping physicalType ODCS → DataType OpenMetadata
PHYSICAL_TYPE_MAP: dict[str, str] = {
    "bigint": "BIGINT",
    "double": "DOUBLE",
    "varchar": "VARCHAR",
    "timestamp(6)": "TIMESTAMP",
}


# ---------------------------------------------------------------------------
# Client HTTP minimal
# ---------------------------------------------------------------------------

def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def fetch(token: str, resource: str, name: str) -> dict | None:
    """GET /{resource}/name/{name} → retourne le JSON si trouvé, None si 404."""
    resp = requests.get(
        f"{OM_BASE}/{resource}/name/{name}",
        headers=_headers(token),
        timeout=10,
    )
    if resp.status_code == 404:
        return None
    if not resp.ok:
        print(f"  [ERR] GET {resource}/name/{name}: HTTP {resp.status_code}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json()


def get_or_create(token: str, resource: str, fqn: str, payload: dict) -> tuple[dict, bool]:
    """Retourne (entity, created). Utilise PUT (upsert) pour éviter les 409.
    
    PUT crée l'entité si elle n'existe pas, la met à jour sinon (y compris si
    elle a été soft-deleted). Retourne (entity, created) où created=True si
    l'entité vient d'être créée (HTTP 201).
    """
    existing = fetch(token, resource, fqn)
    if existing is not None:
        return existing, False

    # PUT = createOrUpdate : pas de 409 même si l'entité existe ou est soft-deleted
    resp = requests.put(
        f"{OM_BASE}/{resource}",
        json=payload,
        headers=_headers(token),
        timeout=15,
    )

    if not resp.ok:
        print(f"  [ERR] PUT {resource}: HTTP {resp.status_code}", file=sys.stderr)
        print(f"  {resp.text[:500]}", file=sys.stderr)
        resp.raise_for_status()

    created = resp.status_code == 201
    return resp.json(), created


# ---------------------------------------------------------------------------
# Étapes de publication
# ---------------------------------------------------------------------------

def create_service(token: str, odcs: dict) -> tuple[str, str, bool]:
    """Retourne (id, fqn, created)."""
    srv = odcs["servers"][0]
    result, created = get_or_create(token, "services/databaseServices", "athena-flights", {
        "name": "athena-flights",
        "displayName": "Athena – Flights",
        "description": "Service Athena hébergeant les données de vols NYC 2013.",
        "serviceType": "Athena",
        "connection": {
            "config": {
                "type": "Athena",
                "awsConfig": {"awsRegion": srv["regionName"]},
                "s3StagingDir": srv["stagingDir"],
                "workgroup": "primary",
            }
        },
    })
    return result["id"], result["fullyQualifiedName"], created


def create_database(token: str, odcs: dict, service_fqn: str) -> tuple[str, str, bool]:
    """Retourne (id, fqn, created)."""
    srv = odcs["servers"][0]
    db_fqn = f"{service_fqn}.{srv['schema']}"
    result, created = get_or_create(token, "databases", db_fqn, {
        "name": srv["schema"],
        "displayName": srv["schema"],
        "description": (
            f"Catalogue Glue `{srv['catalog']}`, "
            f"base `{srv['schema']}`, région {srv['regionName']}."
        ),
        "service": service_fqn,
    })
    return result["id"], result["fullyQualifiedName"], created


def create_schema(token: str, odcs: dict, db_fqn: str) -> tuple[str, str, bool]:
    """Retourne (id, fqn, created)."""
    srv = odcs["servers"][0]
    schema_fqn = f"{db_fqn}.{srv['schema']}"
    result, created = get_or_create(token, "databaseSchemas", schema_fqn, {
        "name": srv["schema"],
        "displayName": srv["schema"],
        "database": db_fqn,
    })
    return result["id"], result["fullyQualifiedName"], created


def build_columns(table_def: dict) -> list[dict]:
    """Construit la liste de colonnes OM à partir des propriétés ODCS."""
    columns = []
    for prop in table_def["properties"]:
        data_type = PHYSICAL_TYPE_MAP.get(prop["physicalType"], "VARCHAR")
        col: dict = {
            "name": prop["name"],
            "displayName": prop["name"],
            "dataType": PHYSICAL_TYPE_MAP.get(prop["physicalType"], "VARCHAR"),
            "dataTypeDisplay": prop["physicalType"],
            "description": prop.get("description", ""),
        }
        if data_type in {"VARCHAR", "CHAR", "BINARY", "VARBINARY"}:
            col["dataLength"] = 256
        if not prop.get("nullable", True):
            col["constraint"] = "NOT_NULL"
        columns.append(col)
    return columns


def create_table(token: str, odcs: dict, schema_fqn: str) -> tuple[str, str, bool]:
    """Retourne (id, fqn, created)."""
    table_def = odcs["schema"][0]
    table_fqn = f"{schema_fqn}.{table_def['name']}"
    result, created = get_or_create(token, "tables", table_fqn, {
        "name": table_def["name"],
        "displayName": table_def["name"].capitalize(),
        "description": table_def["description"],
        "databaseSchema": schema_fqn,
        "columns": build_columns(table_def),
        "tableConstraints": [
            {"constraintType": "UNIQUE", "columns": ["id"]}
        ],
    })
    return result["id"], result["fullyQualifiedName"], created


def create_domain(token: str, odcs: dict) -> tuple[str, str, bool]:
    """Retourne (id, fqn, created)."""
    result, created = get_or_create(token, "domains", "data-engineering", {
        "name": "data-engineering",
        "displayName": "Data Engineering",
        "description": f"Domaine {odcs['team']['name']}.",
        "domainType": "Source-aligned",
    })
    return result["id"], result["fullyQualifiedName"], created


def create_data_product(
    token: str,
    odcs: dict,
    domain_fqn: str,
    table_id: str,
) -> tuple[dict, bool]:
    """Retourne (entity, created)."""
    desc = odcs["description"]
    product_fqn = f"{domain_fqn}.{odcs['id']}"
    return get_or_create(token, "dataProducts", product_fqn, {
        "name": odcs["id"],
        "displayName": odcs["name"],
        "description": (
            f"{desc['purpose']}\n\n"
            f"**Usage** : {desc['usage']}\n\n"
            f"**Limitations** : {desc['limitations']}"
        ),
        "domains": [domain_fqn],
        "assets": [{"id": table_id, "type": "table"}],
    })


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    odcs = yaml.safe_load(ODCS_PATH.read_text())
    print(f"Contrat chargé : {odcs['name']} v{odcs['version']}")

    print("\nConnexion à OpenMetadata…")
    token = "eyJraWQiOiJHYjM4OWEtOWY3Ni1nZGpzLWE5MmotMDI0MmJrOTQzNTYiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJvcGVuLW1ldGFkYXRhLm9yZyIsInN1YiI6ImFkbWluIiwicm9sZXMiOlsiQWRtaW4iXSwiZW1haWwiOiJhZG1pbkBvcGVuLW1ldGFkYXRhLm9yZyIsImlzQm90IjpmYWxzZSwidG9rZW5UeXBlIjoiUEVSU09OQUxfQUNDRVNTIiwidXNlcm5hbWUiOiJhZG1pbiIsInByZWZlcnJlZF91c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNzczMzk4Njg3LCJleHAiOjE3ODExNzQ2ODd9.ig0KRMN17AQtvvkAJeCUjd4HofKL2JGFV1-AX1nKSTrkO3tNQ7qslmUb4jOD-opOt-gBA4qjsMGDFDpMdkL8hMN6XNC-xpV8kUPFHjPvpXUaEqMsD7aPTqlKxOkHk3Q2ffTwtq-zvp3zJg7rZINB_YBEOMJTH-W5-3uO_bo7hj44jHnpkJjPlXjnRy0yz6bVbZ0naiHgi1VtE_pnRjurO10Lg6Inu0VT3xnw8PYdHjZo7Q6k_614sn6-4ieJMCVlaxsyXFE4TmT_Qo9hleb_gysfzDg6dgT-2uPAVuKVrzte9xeP4yPhDvquERNCzLDqc6EjM8P97MVFYKnjSB7qcA"
    print("✓ Authentifié")

    _, service_fqn, created = create_service(token, odcs)
    print(f"{'✓ créé' if created else '→ existant'} Service       : {service_fqn}")

    _, db_fqn, created = create_database(token, odcs, service_fqn)
    print(f"{'✓ créé' if created else '→ existant'} Database       : {db_fqn}")

    _, schema_fqn, created = create_schema(token, odcs, db_fqn)
    print(f"{'✓ créé' if created else '→ existant'} Schema         : {schema_fqn}")

    table_id, table_fqn, created = create_table(token, odcs, schema_fqn)
    print(f"{'✓ créé' if created else '→ existant'} Table          : {table_fqn}")

    _, domain_fqn, created = create_domain(token, odcs)
    print(f"{'✓ créé' if created else '→ existant'} Domain         : {domain_fqn}")

    dp, created = create_data_product(token, odcs, domain_fqn, table_id)
    dp_fqn = dp["fullyQualifiedName"]
    print(f"{'✓ créé' if created else '→ existant'} DataProduct    : {dp_fqn}")

    print(f"\n→ http://localhost:8585/dataProduct/{dp_fqn}")


if __name__ == "__main__":
    main()
