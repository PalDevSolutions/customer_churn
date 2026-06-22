# Deployment Guide

## Local Development

### 1. Start the server

```bash
uvicorn src.api.app:app --reload
```

The server starts at `http://localhost:8000`.

- `--reload` watches for file changes and restarts automatically
- Remove `--reload` in production

### 2. Verify

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Docker (Local)

### Prerequisites

- Docker Desktop installed and running

### Build and run

```bash
docker compose up --build
```

This builds the image, starts the container, and mounts `data/` and `models/` from your local machine into the container. The server is available at `http://localhost:8000`.

### Stop

```bash
docker compose down
```

### What the volumes do

```yaml
volumes:
  - ./data:/app/data      # processed features readable inside container
  - ./models:/app/models  # model file persists after container restart
```

The image only ships source code. Data and models live outside the image so they survive rebuilds.

### Rebuild after code changes

```bash
docker compose up --build
```

The `requirements.txt` layer is cached — only code changes trigger a full rebuild.

---

## Oracle Cloud Deployment

### One-time server setup

SSH into your Oracle Cloud VM and run:

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin curl
sudo usermod -aG docker $USER
```

Log out and back in so the group change takes effect.

### Open port 8000

In the OCI Console:

1. Networking → Virtual Cloud Networks → your VCN
2. Security Lists → Default Security List
3. Add Ingress Rule:
   - Source CIDR: `0.0.0.0/0`
   - Protocol: TCP
   - Destination Port: `8000`

Also run on the VM:

```bash
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
```

### Deploy

From your local machine (with Docker and SSH access):

```bash
chmod +x deploy.sh
./deploy.sh ubuntu@<your-oracle-ip>
```

#### What `deploy.sh` does

| Step | Action |
|---|---|
| 1 | `docker build` — builds the image locally |
| 2 | `docker save` — exports image to a `.tar.gz` |
| 3 | `scp` — copies image, `docker-compose.yml`, and `models/` to the VM |
| 4 | SSH → `docker load` — imports the image on the VM |
| 5 | SSH → `docker compose up -d` — starts the container in detached mode |
| 6 | Hits `/health` and prints the live URL |

### Verify the deployment

```bash
curl http://<your-oracle-ip>:8000/health
# {"status":"ok"}
```

Open `http://<your-oracle-ip>:8000/docs` in a browser.

---

## Re-deploying After Model Updates

If you retrain the model locally:

```bash
./deploy.sh ubuntu@<your-oracle-ip>
```

The script copies the updated `models/baseline_lgb.txt` to the server and restarts the container.

Alternatively, if the server already has the API running, hit the train endpoint to retrain in place:

```bash
curl -X POST http://<your-oracle-ip>:8000/pipeline/train
curl http://<your-oracle-ip>:8000/pipeline/jobs/<job_id>
# wait for "done"
```

The model reloads into memory automatically after training completes — no restart needed.

---

## Container Health Check

`docker-compose.yml` includes:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  retries: 3
```

Docker marks the container unhealthy if `/health` fails 3 times in a row. Check status with:

```bash
docker ps
# Look at the STATUS column — "healthy" vs "unhealthy"
```

---

## File Layout on the Server

After deployment, the VM directory looks like:

```
~/churn/
├── docker-compose.yml
├── data/
│   └── processed/
│       └── train_features.parquet    ← volume-mounted into container
└── models/
    ├── baseline_lgb.txt              ← volume-mounted into container
    ├── feature_importance.png
    └── predictions.csv
```

The Docker image does **not** contain data or models — they are injected at runtime via volume mounts.
