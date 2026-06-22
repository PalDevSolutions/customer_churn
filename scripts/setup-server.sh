#!/usr/bin/env bash
# One-shot Oracle Cloud VM setup script.
# Run as root (or with sudo) on a fresh Ubuntu 22.04 instance.
# Usage: sudo bash setup-server.sh
set -euo pipefail

# ── 1. System update ──────────────────────────────────────────────────────
echo "==> Updating system packages..."
apt-get update -y && apt-get upgrade -y

# ── 2. Install Docker (official repo — NOT the snap version) ─────────────
echo "==> Installing Docker..."
apt-get install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

systemctl enable docker
systemctl start docker

# ── 3. Allow ubuntu user to run Docker without sudo ───────────────────────
usermod -aG docker ubuntu
echo "==> Docker installed — $(docker --version)"

# ── 4. Install utility tools ──────────────────────────────────────────────
echo "==> Installing utilities..."
apt-get install -y curl git htop iptables-persistent

# ── 5. Open ports in the OS firewall ─────────────────────────────────────
# OCI Security Lists handle the cloud-level firewall; Ubuntu's iptables
# adds a second layer that also needs to allow traffic.
echo "==> Configuring iptables..."
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT  # API
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80   -j ACCEPT  # HTTP (future nginx)
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443  -j ACCEPT  # HTTPS (future nginx)
netfilter-persistent save

# ── 6. Create app directory structure ─────────────────────────────────────
echo "==> Creating directory structure..."
mkdir -p /opt/customer-churn/{dev,prod}
mkdir -p /mnt/customer-churn/data/processed
mkdir -p /mnt/customer-churn/models

chown -R ubuntu:ubuntu /opt/customer-churn
chown -R ubuntu:ubuntu /mnt/customer-churn

# ── 7. Summary ────────────────────────────────────────────────────────────
echo ""
echo "=============================="
echo " Server setup complete!"
echo "=============================="
echo " Docker:  $(docker --version)"
echo " Compose: $(docker compose version)"
echo ""
echo " IMPORTANT: Log out and back in so the docker group takes effect."
echo " Then run your deploy script or: docker compose up -d"
