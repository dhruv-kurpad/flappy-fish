#!/usr/bin/env bash
# Test deploy.yml Docker build steps locally (no push, no Azure deploy).
set -euo pipefail

cd /workspace 2>/dev/null || cd "$(dirname "$0")/.."

echo "=== Testing GitHub deploy.yml build steps (local --load) ==="

echo "[1/3] Frontend (context: ./frontend)"
docker buildx build \
  --platform linux/amd64 \
  -t flappyfish-frontend:test \
  -f frontend/Dockerfile.react \
  --load ./frontend

echo "[2/3] Flask API (context: ./src)"
docker buildx build \
  --platform linux/amd64 \
  -t flappyfish-flask-api:test \
  -f src/Dockerfile.web \
  --load ./src

echo "[3/3] Game server (context: ./src)"
docker buildx build \
  --platform linux/amd64 \
  -t flappyfish-game-server:test \
  -f src/Dockerfile.game \
  --load ./src

echo ""
echo "All three images built successfully."
echo "  flappyfish-frontend:test"
echo "  flappyfish-flask-api:test"
echo "  flappyfish-game-server:test"
echo ""
echo "Skipped: az login, ACR push, azuredeploy.json (need secrets)"
