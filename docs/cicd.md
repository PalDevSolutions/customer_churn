# CI/CD Pipeline

## Overview

```
PR / push
    │
    ▼
┌─────────────────────────────────────┐
│  ci.yml  (CI)                       │  ← fast PR gate on main
│  validate.yml  (Validate)           │  ← full gate on all PRs + release/**
└─────────────────────────────────────┘
    │
    │  validate passes on release/**
    ▼
┌─────────────────────────────────────┐
│  deploy-dev.yml  (Deploy Dev)       │  ← upload source → dev VPS
└─────────────────────────────────────┘

git tag v*.*.*
    │
    ▼
┌─────────────────────────────────────┐
│  release.yml  (Release)             │  ← build Docker → GHCR → prod VPS
└─────────────────────────────────────┘
```

---

## Workflows

### `ci.yml` — CI

**Triggers:** PRs to `main`, pushes to `main`

Quick quality gate that blocks broken code from reaching `main`. Runs on every PR.

| Step | Tool | What it checks |
|---|---|---|
| Install | `pip install -e ".[dev]"` | Package resolves cleanly |
| Build check | `python -c "from src.api.app import app"` | All imports succeed |
| Format | `ruff format --check` | Code is consistently formatted |
| Lint | `ruff check` | No style/import/unused-var errors |
| Test | `pytest tests/ -v` | 46 tests pass |

---

### `validate.yml` — Validate

**Triggers:** All PRs, pushes to `main` and `release/**`

Same steps as CI, but also runs on `release/**` branches. **This is the workflow that `deploy-dev` listens to** — a successful run on a `release/**` branch automatically kicks off a dev deployment.

---

### `deploy-dev.yml` — Deploy Development

**Triggers:** `Validate` workflow completes successfully on a `release/**` branch

**What it does:**
1. Sets up SSH access to the dev VPS
2. Uploads the source tree via `tar` over SSH (excludes `.git`, `venv`, `__pycache__`, raw data)
3. Writes `.env.dev` from the `DEV_ENV_FILE` secret
4. Runs `deploy/deploy-dev.sh` on the VPS, which:
   - Creates/updates a Python venv
   - Installs dependencies with `pip install -e ".[dev]"`
   - Restarts the service (Docker Compose or systemd)
   - Runs a health check against `GET /health`

**Concurrency:** Only one dev deployment runs at a time. A new push to the same branch cancels any in-progress deployment.

**Required secrets:**

| Secret | Description |
|---|---|
| `VPS_SSH_KEY` | Private SSH key for the VPS (add the public key to `~/.ssh/authorized_keys`) |
| `VPS_HOST` | IP address or hostname of the dev VPS |
| `VPS_USER` | SSH username (e.g. `ubuntu`) |
| `DEV_ENV_FILE` | Full contents of `.env.dev` — environment variables for the dev container |

---

### `release.yml` — Release

**Triggers:** Push to a version tag `v*.*.*`, or manual dispatch from the Actions tab

**Jobs:**

#### `build-and-push`
1. Logs in to GitHub Container Registry (GHCR) using `GITHUB_TOKEN`
2. Builds the Docker image from `Dockerfile`
3. Pushes two tags:
   - `ghcr.io/<org>/<repo>:v1.2.3` — version-pinned
   - `ghcr.io/<org>/<repo>:latest` — rolling latest

Docker layer caching (`type=gha`) is used so rebuilds after small code changes are fast.

#### `deploy`
1. Copies `deploy/` directory to the production VPS using `appleboy/scp-action`
2. SSHes into the VPS and runs `deploy-prod.sh`, which:
   - Authenticates to GHCR with `GHCR_PAT`
   - Pulls the versioned image
   - Runs `docker compose up -d` (zero-downtime rolling restart)
   - Runs a health check — rolls back if it fails
   - Prunes dangling images

**Required secrets:**

| Secret | Description |
|---|---|
| `VPS_SSH_KEY` | Private SSH key for the production VPS |
| `VPS_HOST` | IP or hostname of the production VPS |
| `VPS_USER` | SSH username |
| `SSH_PORT` | SSH port (usually `22`) |
| `GHCR_PAT` | Personal access token with `read:packages` scope, for pulling images on the VPS |
| `PROD_ENV_FILE` | Full contents of the production `.env` file |

---

## Branch Strategy

```
main           ← stable, protected. CI runs on every PR.
release/x.y    ← release candidate branch. Validate + dev deploy run here.
feature/*      ← development branches. Validate runs on PR only.
```

When you're ready to release:
1. Cut a `release/1.2` branch from `main`
2. Push → Validate runs → dev deployment fires automatically
3. Test on dev VPS
4. Merge to `main`
5. Tag: `git tag v1.2.0 && git push origin v1.2.0`
6. Release workflow fires → Docker image built → production deployed

---

## Deploy Files

| File | Purpose |
|---|---|
| `deploy/deploy-dev.sh` | Runs on dev VPS — installs deps, restarts service |
| `deploy/deploy-prod.sh` | Runs on prod VPS — pulls image, rolling restart, health check |
| `deploy/compose.dev.yml` | Docker Compose for dev (port 8001, bind-mounts source) |
| `deploy/compose.prod.yml` | Docker Compose for prod (port 8000, uses GHCR image) |

---

## Adding Secrets

Go to: `GitHub repo → Settings → Secrets and variables → Actions → New repository secret`

Add each secret from the tables above. The pipeline will silently skip optional steps (like writing `.env.dev`) if the secret is empty.

---

## Manual Release

To release a specific version without tagging:

1. Go to `Actions → Release → Run workflow`
2. Enter the version (e.g. `v1.2.3-rc1`)
3. Toggle "Deploy to VPS" as needed
4. Click Run

---

## Local Equivalent

```bash
# What CI does
make check

# What dev deploy does (locally)
make run

# What release does (locally)
make docker-build
make docker-up
```
