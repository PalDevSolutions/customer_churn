#!/usr/bin/env bash
# Dev deployment — runs on the VPS after source is uploaded by deploy-dev.yml
set -euo pipefail

BRANCH_NAME=${BRANCH_NAME:-unknown}
DEPLOY_SHA=${DEPLOY_SHA:-unknown}
APP_DIR=${APP_DIR:-/opt/customer-churn/dev}

echo "==> Deploying $BRANCH_NAME (${DEPLOY_SHA:0:7}) to dev..."
cd "$APP_DIR"

# Create or update virtual environment
if [ ! -f venv/bin/python ]; then
  echo "==> Creating venv..."
  python3 -m venv venv
fi

echo "==> Installing dependencies..."
venv/bin/pip install -e ".[dev]" --quiet

# Restart via Docker Compose if available, else fall back to systemd
if command -v docker &>/dev/null && [ -f deploy/compose.dev.yml ]; then
  echo "==> Restarting containers..."
  docker compose -f deploy/compose.dev.yml --env-file .env.dev up -d --build --remove-orphans
  sleep 3
  docker compose -f deploy/compose.dev.yml ps
else
  echo "==> Restarting systemd service..."
  systemctl restart customer-churn-dev
fi

# Health check
echo "==> Health check..."
for i in $(seq 1 10); do
  if curl -sf http://localhost:8001/health > /dev/null; then
    echo "==> Health check passed"
    break
  fi
  echo "   waiting... ($i/10)"
  sleep 3
done

echo "==> Dev deployment complete: $BRANCH_NAME @ ${DEPLOY_SHA:0:7}"
