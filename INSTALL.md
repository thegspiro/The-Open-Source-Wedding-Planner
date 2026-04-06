# Installation Guide

This guide covers every way to install and run Wedding Organizer.

## Table of Contents

- [Quick Start (Docker)](#quick-start-docker)
- [Environment Configuration](#environment-configuration)
- [Local Development (Without Docker)](#local-development-without-docker)
- [Production Deployment](#production-deployment)
- [Database Backups](#database-backups)
- [Updating](#updating)
- [Platform-Specific Guides](#platform-specific-guides)

---

## Quick Start (Docker)

The fastest way to get running. Requires [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2.17+ (included with Docker Desktop, or install the [Compose plugin](https://docs.docker.com/compose/install/linux/)).

> **Check your version:** `docker compose version` - you need v2.17.0 or later for the optional `.env` file support. If you're on an older version, see [Older Docker Compose versions](#older-docker-compose-versions) below.

```bash
# Clone the repository
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

# Copy and configure environment
cp .env.example .env
# Edit .env and set a secure SECRET_KEY (see below)

# Start the application
docker-compose up -d
```

Access at: **http://localhost:5000**

### Generate a Secret Key

You must change the `SECRET_KEY` in `.env` before running in production:

```bash
# Option 1: Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Option 2: OpenSSL
openssl rand -hex 32
```

Copy the output into your `.env` file as `SECRET_KEY=<generated-value>`.

---

## Environment Configuration

All configuration is done via environment variables. Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session encryption key | `change-me-...` (insecure) |

### Optional: Email (SMTP)

Enable automated task reminders and guest emails:

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username/email | `you@gmail.com` |
| `SMTP_PASSWORD` | SMTP password or app password | `abcd-efgh-ijkl-mnop` |
| `FROM_EMAIL` | Sender email address | `you@gmail.com` |

**Gmail setup:**
1. Enable 2FA at https://myaccount.google.com/security
2. Generate an app password at https://myaccount.google.com/apppasswords
3. Use the 16-character app password as `SMTP_PASSWORD`

**Other providers:** See `.env.example` for Outlook, Amazon SES, and SendGrid examples.

---

## Local Development (Without Docker)

### Prerequisites

- Python 3.10 or later
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your SECRET_KEY

# Run the application
python app.py
```

Access at: **http://localhost:5000**

The SQLite database is automatically created at `instance/wedding_organizer.db`.

### Running with Gunicorn (Production-like)

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 app:app
```

---

## Production Deployment

### Security Checklist

Before exposing to the internet:

- [ ] Generate and set a strong `SECRET_KEY`
- [ ] Set up a reverse proxy with SSL/TLS (see [docs/REVERSE-PROXY.md](docs/REVERSE-PROXY.md))
- [ ] Configure automated backups (see [Database Backups](#database-backups))
- [ ] Restrict port 5000 to the reverse proxy only (don't expose directly)
- [ ] Review firewall rules

### Reverse Proxy / SSL

For HTTPS and custom domains, put a reverse proxy in front of the application. We provide ready-to-use configurations for:

- **Nginx** + Let's Encrypt
- **Traefik** (automatic SSL)
- **Caddy** (simplest SSL)
- **Cloudflare Tunnel** (no port forwarding needed)

See **[docs/REVERSE-PROXY.md](docs/REVERSE-PROXY.md)** for full configurations.

### Health Check

The application exposes a `/health` endpoint that returns:
- `200 OK` with `{"status": "healthy", "database": "connected"}` when running normally
- `503 Service Unavailable` when the database is unreachable

The Docker image includes a built-in `HEALTHCHECK` that polls this endpoint every 30 seconds.

---

## Database Backups

### Manual Backup

```bash
# Copy the database file
cp instance/wedding_organizer.db backups/wedding_organizer_$(date +%Y%m%d).db
```

### Automated Backup Script

A backup script is included at `scripts/backup.sh`:

```bash
# Make it executable
chmod +x scripts/backup.sh

# Create a backup
./scripts/backup.sh

# Backup to a custom directory
./scripts/backup.sh /mnt/backups

# Restore from the latest backup
./scripts/backup.sh --restore latest

# Restore from a specific backup
./scripts/backup.sh --restore backups/wedding_organizer_20260101_020000.db
```

### Automated Daily Backups (cron)

```bash
# Edit crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /path/to/the-open-source-wedding-planner/scripts/backup.sh /path/to/backups
```

### Docker Volume Backup

```bash
# Backup the Docker volume directly
docker cp wedding-organizer:/app/instance/wedding_organizer.db ./backup.db

# Or tar the entire instance directory
tar czf wedding-backup-$(date +%Y%m%d).tar.gz instance/
```

---

## Updating

### Docker

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Local

```bash
git pull
pip install -r requirements.txt
# Restart the application
```

> **Note:** The database schema updates automatically on startup. Always back up your database before updating.

---

## Platform-Specific Guides

Detailed guides for running on specific platforms:

| Platform | Guide |
|----------|-------|
| **Docker** (standalone) | This file (above) |
| **Unraid** | [docs/DEPLOYMENT-GUIDES.md - Unraid](docs/DEPLOYMENT-GUIDES.md#unraid) |
| **Proxmox** | [docs/DEPLOYMENT-GUIDES.md - Proxmox](docs/DEPLOYMENT-GUIDES.md#proxmox) |
| **Synology NAS** | [docs/DEPLOYMENT-GUIDES.md - Synology](docs/DEPLOYMENT-GUIDES.md#synology-nas) |
| **Kubernetes** | [docs/DEPLOYMENT-GUIDES.md - Kubernetes](docs/DEPLOYMENT-GUIDES.md#kubernetes) |
| **Raspberry Pi** | [docs/DEPLOYMENT-GUIDES.md - Raspberry Pi](docs/DEPLOYMENT-GUIDES.md#raspberry-pi) |
| **VPS (DigitalOcean, Linode, etc.)** | [docs/DEPLOYMENT-GUIDES.md - VPS](docs/DEPLOYMENT-GUIDES.md#vps-digitalocean-linode-hetzner) |

---

## Docker Commands Reference

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# View logs (last 100 lines)
docker-compose logs --tail=100

# Restart
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# Check health status
docker inspect --format='{{.State.Health.Status}}' wedding-organizer

# Shell into container
docker exec -it wedding-organizer /bin/bash
```

---

## Troubleshooting

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common issues and fixes.

### Common Issues

**Port 5000 already in use:**
```bash
# Change the port mapping in docker-compose.yml
ports:
  - "8080:5000"  # Access at http://localhost:8080
```

**Permission denied on instance/ directory:**
```bash
# Fix ownership
sudo chown -R 1000:1000 instance/
```

**Container won't start:**
```bash
# Check logs for errors
docker-compose logs wedding-organizer

# Verify .env file exists and is valid
cat .env
```

**Older Docker Compose versions:**

If you're on Docker Compose < v2.17, the `required: false` syntax in `docker-compose.yml` won't work. Either:
- Upgrade Docker Compose: `sudo apt install docker-compose-plugin` (Linux) or update Docker Desktop
- Or create an empty `.env` file: `touch .env`
- Or remove the `env_file` block from `docker-compose.yml` and set variables directly in the `environment` section

---

## Building Multi-Architecture Images

The default `docker-compose up --build` builds for your current platform. To build images that run on multiple architectures (e.g., ARM for Raspberry Pi, AMD64 for PCs):

### Using Docker Buildx

```bash
# Create a buildx builder (first time only)
docker buildx create --name multiarch --use

# Build and push a multi-arch image
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t yourdockerhubuser/wedding-organizer:latest \
  --push .
```

### Supported Architectures

| Architecture | Platforms |
|-------------|-----------|
| `linux/amd64` | Standard PCs, most VPS, Intel/AMD servers |
| `linux/arm64` | Raspberry Pi 4/5 (64-bit OS), Apple Silicon, ARM servers |
| `linux/arm/v7` | Raspberry Pi 3, older ARM boards (32-bit) |

The `python:3.11-slim` base image supports all three architectures natively.

### Using a Pre-Built Image

If you've pushed a multi-arch image to a registry, other users can pull it directly instead of building from source:

```yaml
# In docker-compose.yml, replace "build: ." with:
services:
  wedding-organizer:
    image: yourdockerhubuser/wedding-organizer:latest
    # ... rest of config
```
