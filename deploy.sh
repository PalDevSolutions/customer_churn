#!/usr/bin/env bash
set -euo pipefail

SERVER=${1:?"Usage: $0 ubuntu@<oracle-ip>"}

echo "==> Building image..."
docker build -t customer-churn-api:latest .

echo "==> Saving image to tar..."
docker save customer-churn-api:latest | gzip > /tmp/customer-churn-api.tar.gz

echo "==> Copying files to $SERVER..."
scp /tmp/customer-churn-api.tar.gz "$SERVER":/tmp/
scp docker-compose.yml "$SERVER":/tmp/
scp -r models/ "$SERVER":/tmp/models/

echo "==> Deploying on server..."
ssh "$SERVER" << 'REMOTE'
  set -e
  mkdir -p ~/churn/{data/processed,models}
  docker load < /tmp/customer-churn-api.tar.gz
  cp /tmp/docker-compose.yml ~/churn/docker-compose.yml
  cp -r /tmp/models/* ~/churn/models/
  cd ~/churn
  docker compose up -d
  sleep 3
  curl -f http://localhost:8000/health && echo "Service is up!"
REMOTE

SERVER_IP=$(echo "$SERVER" | cut -d@ -f2)
echo "==> Done! Service available at http://$SERVER_IP:8000"
