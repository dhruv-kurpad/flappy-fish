#!/usr/bin/env bash
# Run deploy.yml steps from az login onward (uses deploy.secrets.env locally).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SECRETS_FILE="${SECRETS_FILE:-$ROOT/deploy.secrets.env}"
if [[ ! -f "$SECRETS_FILE" ]]; then
  echo "Missing $SECRETS_FILE — copy deploy.secrets.example and fill in values." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$SECRETS_FILE"
set +a

for var in ACR_LOGIN_SERVER ACR_USERNAME ACR_PASSWORD AZURE_RESOURCE_GROUP \
           SQL_USERNAME SQL_PASSWORD AZURE_CLIENT_ID AZURE_CLIENT_SECRET AZURE_TENANT_ID; do
  if [[ -z "${!var:-}" ]]; then
    echo "Missing required variable: $var" >&2
    exit 1
  fi
done

echo "=== Azure CLI login ==="
az login --service-principal \
  -u "$AZURE_CLIENT_ID" \
  -p "$AZURE_CLIENT_SECRET" \
  --tenant "$AZURE_TENANT_ID" \
  -o none

echo "=== ACR login ==="
echo "$ACR_PASSWORD" | docker login "$ACR_LOGIN_SERVER" \
  --username "$ACR_USERNAME" --password-stdin

echo "=== Build & push frontend ==="
docker buildx build --platform linux/amd64 \
  -t "$ACR_LOGIN_SERVER/frontend:latest" \
  -f frontend/Dockerfile.react --push ./frontend

echo "=== Build & push flask-api ==="
docker buildx build --platform linux/amd64 \
  -t "$ACR_LOGIN_SERVER/flask-api:latest" \
  -f src/Dockerfile.web --push ./src

echo "=== Build & push game-server ==="
docker buildx build --platform linux/amd64 \
  -t "$ACR_LOGIN_SERVER/game-server:latest" \
  -f src/Dockerfile.game --push ./src

echo "=== Deploy to Azure Container Instances ==="
az deployment group create \
  --resource-group "$AZURE_RESOURCE_GROUP" \
  --template-file azuredeploy.json \
  --parameters \
    acrServer="$ACR_LOGIN_SERVER" \
    acrUsername="$ACR_USERNAME" \
    acrPassword="$ACR_PASSWORD" \
    sqlUsername="$SQL_USERNAME" \
    sqlPassword="$SQL_PASSWORD"

echo ""
echo "Deploy complete."
