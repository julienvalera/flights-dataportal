#!/bin/sh
# Lance OpenMetadata en local.
# Télécharge docker-compose.yml depuis le release officiel si absent.
set -e

OM_VERSION="1.12.0-release"
COMPOSE_FILE="$(dirname "$0")/../docker-compose.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Téléchargement de docker-compose.yml (OpenMetadata $OM_VERSION)..."
  curl -sL -o "$COMPOSE_FILE" \
    "https://github.com/open-metadata/OpenMetadata/releases/download/$OM_VERSION/docker-compose.yml"
  echo "OK"
fi

docker compose -f "$COMPOSE_FILE" up -d
echo "OpenMetadata disponible sur http://localhost:8585"
