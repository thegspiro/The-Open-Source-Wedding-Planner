# Platform-Specific Deployment Guides

Step-by-step guides for running Wedding Organizer on popular self-hosting platforms.

**Prerequisites for all platforms:** Familiarity with your platform's basic operations. The application requires ~512 MB RAM and minimal CPU.

## Table of Contents

- [Unraid](#unraid)
- [Proxmox](#proxmox)
- [Synology NAS](#synology-nas)
- [Kubernetes](#kubernetes)
- [Raspberry Pi](#raspberry-pi)
- [VPS (DigitalOcean, Linode, Hetzner)](#vps-digitalocean-linode-hetzner)
- [TrueNAS Scale](#truenas-scale)
- [Docker Swarm](#docker-swarm)

---

## Unraid

Unraid supports Docker containers natively through its web UI.

### Option A: Community Applications (Recommended)

If the Wedding Organizer template is available in Community Applications:

1. Go to **Apps** tab in Unraid
2. Search for "Wedding Organizer"
3. Click **Install**
4. Configure the template (see settings below)
5. Click **Apply**

### Option B: Manual Docker Container

1. Go to **Docker** tab in Unraid
2. Click **Add Container**
3. Fill in the following:

| Field | Value |
|-------|-------|
| **Name** | `wedding-organizer` |
| **Repository** | Build from Dockerfile or use your image |
| **Network Type** | `bridge` |
| **Port Mapping** | Host: `4345` -> Container: `4345` |

4. Add a **Path** mapping:

| Container Path | Host Path | Access Mode |
|----------------|-----------|-------------|
| `/app/instance` | `/mnt/user/appdata/wedding-organizer/` | Read/Write |

5. Add **Variables**:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | (generate with `openssl rand -hex 32`) |
| `SMTP_HOST` | (optional) `smtp.gmail.com` |
| `SMTP_PORT` | (optional) `587` |
| `SMTP_USER` | (optional) your email |
| `SMTP_PASSWORD` | (optional) your app password |

6. Click **Apply**

### Option C: Docker Compose on Unraid

If you have the **Docker Compose Manager** plugin installed:

1. Install the **Compose Manager** plugin from Community Applications
2. SSH into your Unraid server or use the terminal
3. Create a directory:
   ```bash
   mkdir -p /mnt/user/appdata/wedding-organizer
   cd /mnt/user/appdata/wedding-organizer
   ```
4. Clone the repository:
   ```bash
   git clone https://github.com/thegspiro/the-open-source-wedding-planner.git .
   ```
5. Configure environment:
   ```bash
   cp .env.example .env
   nano .env  # Set your SECRET_KEY
   ```
6. Start:
   ```bash
   docker-compose up -d
   ```

### Accessing on Unraid

- **Local:** `http://YOUR_UNRAID_IP:4345`
- **With reverse proxy:** Use Nginx Proxy Manager (available in Community Apps) for SSL and custom domain

### Unraid Backup

Unraid's built-in backup tools will cover the appdata path. Your database lives at:
```
/mnt/user/appdata/wedding-organizer/instance/wedding_organizer.db
```

---

## Proxmox

You can run Wedding Organizer in either an **LXC container** (lightweight) or a **VM** (full isolation).

### Option A: LXC Container (Recommended)

LXC containers use fewer resources than full VMs.

#### 1. Create the LXC Container

```bash
# From Proxmox shell or UI:
# Create an Ubuntu 22.04 LXC container
# Recommended: 1 CPU core, 512 MB RAM, 4 GB disk

# Via CLI:
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname wedding-organizer \
  --memory 512 \
  --cores 1 \
  --rootfs local-lvm:4 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --unprivileged 1 \
  --features nesting=1

pct start 200
```

#### 2. Install Docker Inside LXC

```bash
# Enter the container
pct enter 200

# Update and install Docker
apt update && apt upgrade -y
apt install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

#### 3. Deploy Wedding Organizer

```bash
cd /opt
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

cp .env.example .env
nano .env  # Set SECRET_KEY

docker compose up -d
```

#### 4. Access

`http://LXC_IP_ADDRESS:4345`

Find the IP with: `ip addr show eth0`

### Option B: VM with Docker

1. Create a new VM in the Proxmox UI (Ubuntu Server 22.04)
2. Allocate: 1 CPU, 1 GB RAM, 10 GB disk
3. Install Ubuntu, then follow the [Docker quick start](../INSTALL.md#quick-start-docker)

### Option C: Bare Metal in LXC (No Docker)

```bash
pct enter 200

# Install Python
apt update && apt install -y python3 python3-pip python3-venv git

# Clone and set up
cd /opt
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env  # Set SECRET_KEY

# Run with gunicorn
gunicorn --bind 0.0.0.0:4345 --workers 2 --threads 2 app:app
```

To run as a service, create `/etc/systemd/system/wedding-organizer.service`:

```ini
[Unit]
Description=Wedding Organizer
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/the-open-source-wedding-planner
Environment=PATH=/opt/the-open-source-wedding-planner/venv/bin
ExecStart=/opt/the-open-source-wedding-planner/venv/bin/gunicorn --bind 0.0.0.0:4345 --workers 2 --threads 2 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now wedding-organizer
```

### Proxmox Backup

Use Proxmox Backup Server or vzdump to back up the entire LXC container:
```bash
vzdump 200 --storage local --compress zstd
```

---

## Synology NAS

### Option A: Container Manager (DSM 7.2+)

Synology's Container Manager (formerly Docker) provides a UI for running containers.

1. Open **Container Manager** from the DSM menu
2. Go to **Project** > **Create**
3. Set **Project name** to `wedding-organizer`
4. Set **Path** to a shared folder (e.g., `/docker/wedding-organizer`)
5. Upload or paste the `docker-compose.yml` from this repository
6. Click **Next**, configure environment variables, then **Done**

### Option B: SSH + Docker Compose

```bash
# SSH into your Synology
ssh admin@YOUR_NAS_IP

# Create directory
mkdir -p /volume1/docker/wedding-organizer
cd /volume1/docker/wedding-organizer

# Clone repository
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git .

# Configure
cp .env.example .env
vi .env  # Set SECRET_KEY

# Start
docker-compose up -d
```

### Data Location

Store the database on a reliable volume:
```yaml
volumes:
  - /volume1/docker/wedding-organizer/instance:/app/instance
```

### Access

`http://YOUR_NAS_IP:4345`

---

## Kubernetes

### Basic Deployment

Create `wedding-organizer.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: wedding

---
apiVersion: v1
kind: Secret
metadata:
  name: wedding-secret
  namespace: wedding
type: Opaque
stringData:
  SECRET_KEY: "your-generated-secret-key-here"

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: wedding-data
  namespace: wedding
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wedding-organizer
  namespace: wedding
spec:
  replicas: 1  # SQLite does not support multiple writers
  selector:
    matchLabels:
      app: wedding-organizer
  template:
    metadata:
      labels:
        app: wedding-organizer
    spec:
      containers:
        - name: wedding-organizer
          image: ghcr.io/thegspiro/the-open-source-wedding-planner:latest
          # Or build your own: docker build -t wedding-organizer .
          ports:
            - containerPort: 4345
          env:
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: wedding-secret
                  key: SECRET_KEY
          volumeMounts:
            - name: data
              mountPath: /app/instance
          livenessProbe:
            httpGet:
              path: /health
              port: 4345
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 4345
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: wedding-data

---
apiVersion: v1
kind: Service
metadata:
  name: wedding-organizer
  namespace: wedding
spec:
  selector:
    app: wedding-organizer
  ports:
    - port: 80
      targetPort: 4345
  type: ClusterIP

---
# Optional: Ingress for external access
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: wedding-ingress
  namespace: wedding
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod  # If using cert-manager
spec:
  tls:
    - hosts:
        - wedding.yourdomain.com
      secretName: wedding-tls
  rules:
    - host: wedding.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: wedding-organizer
                port:
                  number: 80
```

### Deploy

```bash
kubectl apply -f wedding-organizer.yaml
```

### Important Notes

- **Replicas must be 1** - SQLite does not support concurrent writers. If you need horizontal scaling, migrate to PostgreSQL.
- Use a `PersistentVolumeClaim` to persist the SQLite database.
- The `/health` endpoint is used for liveness and readiness probes.

### Helm Chart

No official Helm chart exists yet. Contributions welcome!

---

## Raspberry Pi

Wedding Organizer runs well on Raspberry Pi 3B+ or newer.

### Prerequisites

- Raspberry Pi 3B+ or newer (Pi 4/5 recommended)
- Raspberry Pi OS (64-bit recommended)
- At least 1 GB RAM

### Option A: Docker on Pi

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in

# Clone and run
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner
cp .env.example .env
nano .env  # Set SECRET_KEY

docker compose up -d
```

> The Docker image builds natively on ARM64. For Pi 3 (armv7l), the `python:3.11-slim` base image supports both architectures.

### Option B: Native Python on Pi

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env

# Run
gunicorn --bind 0.0.0.0:4345 --workers 2 --threads 2 app:app
```

### Run as a Service

Create `/etc/systemd/system/wedding-organizer.service`:

```ini
[Unit]
Description=Wedding Organizer
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/the-open-source-wedding-planner
Environment=PATH=/home/pi/the-open-source-wedding-planner/venv/bin
EnvironmentFile=/home/pi/the-open-source-wedding-planner/.env
ExecStart=/home/pi/the-open-source-wedding-planner/venv/bin/gunicorn --bind 0.0.0.0:4345 --workers 2 --threads 2 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wedding-organizer
```

### Access

`http://RASPBERRY_PI_IP:4345`

---

## VPS (DigitalOcean, Linode, Hetzner)

### Recommended Specs

- **OS:** Ubuntu 22.04 or Debian 12
- **RAM:** 1 GB minimum
- **CPU:** 1 vCPU
- **Disk:** 10 GB SSD

### Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Clone repository
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

# Configure
cp .env.example .env
nano .env  # Set a strong SECRET_KEY

# Start
docker compose up -d
```

### Firewall Setup

```bash
# Allow SSH and HTTP/HTTPS
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Don't expose port 4345 directly - use a reverse proxy
```

### Add SSL with Caddy (Simplest)

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy

# Configure Caddy
sudo tee /etc/caddy/Caddyfile <<EOF
wedding.yourdomain.com {
    reverse_proxy localhost:4345
}
EOF

sudo systemctl restart caddy
```

Caddy automatically provisions and renews Let's Encrypt SSL certificates.

See [docs/REVERSE-PROXY.md](REVERSE-PROXY.md) for nginx, Traefik, and Cloudflare Tunnel options.

### Automated Backups on VPS

```bash
# Make backup script executable
chmod +x scripts/backup.sh

# Daily backup at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * cd /root/the-open-source-wedding-planner && ./scripts/backup.sh") | crontab -
```

---

## TrueNAS Scale

TrueNAS Scale supports Docker containers through its Apps system.

### Custom App Deployment

1. Go to **Apps** > **Discover Apps** > **Custom App**
2. Configure:
   - **Application Name:** `wedding-organizer`
   - **Image Repository:** Build from source or use your own registry
   - **Container Port:** `4345`
3. Add **Host Path Volume:**
   - **Host Path:** `/mnt/pool/apps/wedding-organizer/instance`
   - **Mount Path:** `/app/instance`
4. Add **Environment Variables:**
   - `SECRET_KEY` = your generated key
5. Start the application

### Docker Compose on TrueNAS Scale

```bash
# SSH into TrueNAS Scale
cd /mnt/pool/apps
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

cp .env.example .env
nano .env

docker compose up -d
```

---

## Docker Swarm

For high-availability setups (note: SQLite limits this to a single replica).

```yaml
# docker-stack.yml
version: "3.8"

services:
  wedding-organizer:
    image: wedding-organizer:latest
    build: .
    ports:
      - "4345:4345"
    volumes:
      - wedding-data:/app/instance
    environment:
      - SECRET_KEY_FILE=/run/secrets/secret_key
    secrets:
      - secret_key
    deploy:
      replicas: 1  # Must be 1 due to SQLite
      restart_policy:
        condition: on-failure
      resources:
        limits:
          memory: 512M

secrets:
  secret_key:
    external: true

volumes:
  wedding-data:
    driver: local
```

```bash
# Create the secret
echo "your-secret-key" | docker secret create secret_key -

# Deploy the stack
docker stack deploy -c docker-stack.yml wedding
```

---

## Need Help?

- **General issues:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
- **Installation:** [INSTALL.md](../INSTALL.md)
- **Reverse proxy / SSL:** [docs/REVERSE-PROXY.md](REVERSE-PROXY.md)
- **Feature docs:** [docs/WIKI.md](WIKI.md)
