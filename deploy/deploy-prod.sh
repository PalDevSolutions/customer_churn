#!/usr/bin/env bash
# Production blue/green deployment — runs on the VPS via release.yml
set -euo pipefail

VERSION=${1:?"Usage: $0 <version>"}
APP_DIR="/opt/customer-churn/prod"

echo "==> Deploying $VERSION to production..."

# Authenticate to GHCR
echo "$GHCR_PAT" | docker login ghcr.io -u "$GHCR_USER" --password-stdin

# Pull the versioned image
echo "==> Pulling $IMAGE_TAG..."
docker pull "$IMAGE_TAG"

# Update running containers (Docker Compose handles rolling restart)
cd "$APP_DIR"
export IMAGE_TAG="$IMAGE_TAG"
docker compose -f compose.prod.yml up -d --no-build --remove-orphans

# Health check with retry
echo "==> Waiting for health check..."
for i in $(seq 1 15); do
  if curl -sf http://localhost:8000/health > /dev/null; then
    echo "==> Health check passed"
    break
  fi
  if [ "$i" -eq 15 ]; then
    echo "==> Health check failed — rolling back..."
    docker compose -f compose.prod.yml up -d --no-build --remove-orphans
    exit 1
  fi
  echo "   waiting... ($i/15)"
  sleep 4
done

# Prune dangling images to save disk space
docker image prune -f

echo "==> Production deployment complete: $VERSION"
