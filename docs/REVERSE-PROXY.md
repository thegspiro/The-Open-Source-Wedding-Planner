# Reverse Proxy Configuration

This guide covers setting up a reverse proxy in front of Wedding Organizer for SSL/TLS termination, custom domains, and production hardening.

## Why Use a Reverse Proxy?

- **HTTPS/SSL** - Encrypt traffic with Let's Encrypt certificates
- **Custom domain** - Access via `wedding.yourdomain.com` instead of `IP:5000`
- **Security** - Hide the application server, add rate limiting
- **Performance** - Static file caching, compression

---

## Required: set `TRUST_PROXY=true`

**Set this whenever the app runs behind a proxy.** Add it to your `.env`:

```bash
TRUST_PROXY=true
```

Behind a proxy, every request reaches the app from the proxy's address. Without
`TRUST_PROXY` the app takes that address at face value, so all visitors look
like a single client and share one rate-limit bucket. The practical effect is
that ten failed logins — from anyone, anywhere — lock out **every user** for
five minutes, and that condition can be held indefinitely.

With `TRUST_PROXY=true` the app reads the real client address from
`X-Forwarded-For`, and rate limits apply per visitor as intended.

Your proxy must set that header (every configuration in this guide already
does):

```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

**Leave it unset when the app is exposed directly.** `X-Forwarded-For` is just a
request header, so anyone can forge it. With no proxy in front to overwrite it,
trusting the header would let an attacker present a different IP on every
request and bypass rate limiting entirely.

---

## Option 1: Nginx

### Basic Configuration

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name wedding.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name wedding.yourdomain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/wedding.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/wedding.yourdomain.com/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy to Wedding Organizer
    location / {
        proxy_pass http://wedding-organizer:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Cache static files
    location /static/ {
        proxy_pass http://wedding-organizer:5000/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

### Docker Compose with Nginx

```yaml
services:
  wedding-organizer:
    build: .
    container_name: wedding-organizer
    env_file: .env
    volumes:
      - ./instance:/app/instance
    restart: unless-stopped
    # No need to expose port 5000 externally

  nginx:
    image: nginx:alpine
    container_name: wedding-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - wedding-organizer
    restart: unless-stopped

  # Auto-renew SSL certificates
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

### Initial SSL Certificate Setup

```bash
# First, set up nginx without SSL (comment out the 443 server block)
# Then run certbot:
docker-compose run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  -d wedding.yourdomain.com \
  --email your-email@example.com \
  --agree-tos

# Enable the 443 server block and restart
docker-compose restart nginx
```

---

## Option 2: Traefik (Automatic SSL)

Traefik automatically manages Let's Encrypt certificates.

### Docker Compose with Traefik

```yaml
services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    restart: unless-stopped

  wedding-organizer:
    build: .
    container_name: wedding-organizer
    env_file: .env
    volumes:
      - ./instance:/app/instance
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.wedding.rule=Host(`wedding.yourdomain.com`)"
      - "traefik.http.routers.wedding.entrypoints=websecure"
      - "traefik.http.routers.wedding.tls.certresolver=letsencrypt"
      - "traefik.http.services.wedding.loadbalancer.server.port=5000"
    restart: unless-stopped
```

This is the easiest option - Traefik handles SSL certificates automatically.

---

## Option 3: Caddy (Simplest SSL)

Caddy automatically provisions and renews SSL certificates with zero configuration.

### Caddyfile

```
wedding.yourdomain.com {
    reverse_proxy wedding-organizer:5000

    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    @static path /static/*
    handle @static {
        header Cache-Control "public, max-age=604800, immutable"
        reverse_proxy wedding-organizer:5000
    }
}
```

### Docker Compose with Caddy

```yaml
services:
  wedding-organizer:
    build: .
    container_name: wedding-organizer
    env_file: .env
    volumes:
      - ./instance:/app/instance
    restart: unless-stopped

  caddy:
    image: caddy:2-alpine
    container_name: wedding-caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./caddy_data:/data
      - ./caddy_config:/config
    depends_on:
      - wedding-organizer
    restart: unless-stopped
```

---

## LAN-Only Access (No SSL)

If running on a home network without a domain, use a simple nginx proxy:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://wedding-organizer:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Or access directly at `http://YOUR_SERVER_IP:5000`.

---

## Cloudflare Tunnel (No Port Forwarding)

For exposing the application without opening firewall ports:

```bash
# Install cloudflared
docker run -d --name cloudflared \
  --network container:wedding-organizer \
  cloudflare/cloudflared:latest \
  tunnel --no-autoupdate run --token YOUR_TUNNEL_TOKEN
```

Configure the tunnel in the Cloudflare Zero Trust dashboard to point to `http://localhost:5000`.
