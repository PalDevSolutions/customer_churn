# Oracle Cloud Setup Guide

End-to-end guide to provision a free Oracle Cloud VM, prepare it for Docker, and deploy the customer churn API.

---

## 1. Create an Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and click **Start for free**
2. Fill in your details — you need a credit card for identity verification (you won't be charged for Always Free resources)
3. Choose your **Home Region** — pick the one closest to you; **you cannot change it later**
4. Complete email verification and sign in to the console

---

## 2. Create a Compute Instance

### 2.1 Open the instance wizard

`Console → Hamburger menu (☰) → Compute → Instances → Create instance`

### 2.2 Configure the instance

| Field | Value |
|---|---|
| **Name** | `customer-churn-api` |
| **Image** | Canonical Ubuntu 22.04 (click *Change image*) |
| **Shape** | VM.Standard.E2.1.Micro — 1 OCPU, 1 GB RAM (**Always Free**) |

> **Tip — want more RAM for free?**  
> Choose **VM.Standard.A1.Flex** (ARM) instead: up to 4 OCPU + 24 GB RAM across all your A1 instances, still Always Free. The Docker image and CI pipeline would need ARM64 builds (`--platform linux/arm64`). For now, E2.1.Micro is simpler.

### 2.3 Networking

- Leave **Primary network** on the auto-created VCN
- Leave **Public IPv4 address** set to **Assign a public IPv4 address** — you need this to reach the server

### 2.4 SSH key

- Select **Generate a key pair for me**
- Download both keys immediately — you cannot retrieve the private key again
- Save as `~/.ssh/oracle_churn.pem`
- `chmod 400 ~/.ssh/oracle_churn.pem`

### 2.5 Create

Click **Create**. The instance moves from `PROVISIONING` to `RUNNING` in about 2 minutes.

**Note the public IP address** from the instance detail page — you'll need it for SSH and for GitHub secrets.

---

## 3. Open Port 8000 in OCI Security Lists

By default OCI only allows SSH (port 22). You must explicitly open port 8000.

`Console → Networking → Virtual Cloud Networks → your-VCN → Security Lists → Default Security List → Add Ingress Rules`

Add these two rules:

| Source CIDR | Protocol | Destination Port | Description |
|---|---|---|---|
| `0.0.0.0/0` | TCP | `8000` | Customer Churn API |
| `0.0.0.0/0` | TCP | `80` | HTTP (for future nginx) |

Click **Add Ingress Rules**.

> The OS-level firewall (iptables) is handled by the setup script in step 4.

---

## 4. SSH Into the Instance and Run the Setup Script

```bash
# Connect
ssh -i ~/.ssh/oracle_churn.pem ubuntu@<YOUR_PUBLIC_IP>

# Download and run the setup script (one-time)
curl -fsSL https://raw.githubusercontent.com/<your-org>/customer-churn/main/scripts/setup-server.sh \
  | sudo bash

# Or upload from your local machine and run:
scp -i ~/.ssh/oracle_churn.pem scripts/setup-server.sh ubuntu@<YOUR_PUBLIC_IP>:~
ssh -i ~/.ssh/oracle_churn.pem ubuntu@<YOUR_PUBLIC_IP> "sudo bash ~/setup-server.sh"
```

The script:
- Updates Ubuntu packages
- Installs Docker (from the official Docker repo, not snap)
- Installs `docker-compose-plugin`
- Opens ports 8000, 80, 443 in iptables and persists the rules
- Creates `/opt/customer-churn/{dev,prod}` and `/mnt/customer-churn/{data,models}`

**After the script finishes, log out and back in** so the `docker` group takes effect:

```bash
exit
ssh -i ~/.ssh/oracle_churn.pem ubuntu@<YOUR_PUBLIC_IP>
docker ps   # should work without sudo
```

---

## 5. First Manual Deployment

Before CI/CD is wired up, verify the server works with a manual deploy:

```bash
# From your local machine (project root)
./deploy.sh ubuntu@<YOUR_PUBLIC_IP>
```

What this does:
1. `docker build` locally
2. `docker save` → gzip tar
3. `scp` image + compose file + models to the VM
4. SSH → `docker load` + `docker compose up -d`
5. Hits `/health` and prints the live URL

Then open: `http://<YOUR_PUBLIC_IP>:8000/docs`

---

## 6. Wire Up GitHub Secrets

Once the manual deploy works, add secrets to GitHub so the CI/CD workflows can deploy automatically.

`GitHub repo → Settings → Secrets and variables → Actions → New repository secret`

### Secrets for `deploy-dev.yml`

| Secret name | Value |
|---|---|
| `VPS_SSH_KEY` | Contents of `~/.ssh/oracle_churn.pem` (the private key) |
| `VPS_HOST` | `<YOUR_PUBLIC_IP>` |
| `VPS_USER` | `ubuntu` |
| `DEV_ENV_FILE` | (leave empty for now — add env vars here when you have them) |

### Additional secrets for `release.yml`

| Secret name | Value |
|---|---|
| `SSH_PORT` | `22` |
| `GHCR_PAT` | GitHub Personal Access Token with `read:packages` and `write:packages` scopes |
| `PROD_ENV_FILE` | (leave empty for now) |

**How to create GHCR_PAT:**  
`GitHub → Settings (your profile) → Developer settings → Personal access tokens → Tokens (classic) → Generate new token`  
Scopes: `read:packages`, `write:packages`, `delete:packages`

---

## 7. Set Up the CI/CD Flow

Once secrets are added:

| Trigger | What happens |
|---|---|
| Push to `release/**` branch | `validate.yml` runs → on success, `deploy-dev.yml` deploys to the VM |
| `git tag v1.0.0 && git push origin v1.0.0` | `release.yml` builds Docker image, pushes to GHCR, deploys to prod |

Test it:
```bash
git checkout -b release/1.0
git push origin release/1.0
# Watch Actions tab — Validate then Deploy Development should both turn green
```

---

## 8. Useful Server Commands

```bash
# SSH into the VM
ssh -i ~/.ssh/oracle_churn.pem ubuntu@<YOUR_PUBLIC_IP>

# Check running containers
docker ps

# View API logs
docker compose logs -f

# Restart the API
docker compose restart

# Check health
curl http://localhost:8000/health

# Check disk usage
df -h
docker system df
```

---

## 9. Free Tier Limits

| Resource | Always Free allowance |
|---|---|
| VM.Standard.E2.1.Micro | 2 instances, 1/8 OCPU, 1 GB RAM each |
| VM.Standard.A1.Flex | 4 OCPU + 24 GB RAM total across all A1 instances |
| Block storage | 2 × 50 GB boot volumes |
| Outbound data transfer | 10 TB/month |
| Object storage | 20 GB |

The E2.1.Micro with 1 GB RAM is tight for running Docker + LightGBM inference simultaneously. If you hit OOM errors, either:
- Switch to A1.Flex (better free tier), or
- Add a 1 GB swap file:

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
