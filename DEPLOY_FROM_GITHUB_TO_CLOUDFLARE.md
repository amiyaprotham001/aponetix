# Deploy APONETIX from GitHub to Cloudflare (Recommended Model)

Repository:
- https://github.com/amiyaprotham001/aponetix

This Flask app should be deployed to an origin server first, then proxied through Cloudflare.

## Architecture
1. GitHub repo -> GitHub Actions
2. GitHub Actions -> Origin server (SSH deploy)
3. Origin server -> Nginx + Waitress app
4. Cloudflare -> DNS proxy + SSL + WAF

## Files Already Added
- `.github/workflows/deploy-origin.yml`
- `deploy/aponetix.service`
- `deploy/nginx-aponetix.conf`

## Step 1: Prepare origin server (Ubuntu)
- Create app folder:
  - `/opt/aponetix`
- Clone repo:
  - `git clone https://github.com/amiyaprotham001/aponetix /opt/aponetix`
- Create venv and install deps:
  - `python3 -m venv /opt/aponetix/.venv`
  - `/opt/aponetix/.venv/bin/pip install -r /opt/aponetix/requirements.txt`

## Step 2: Set production env file
Create `/opt/aponetix/.env` with strong values:

APP_ENV=production
FLASK_SECRET_KEY=CHANGE_TO_LONG_RANDOM_SECRET
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=1
TRUST_PROXY=1
SITE_URL=https://aponetix.tech
ALLOWED_HOSTS=aponetix.tech,www.aponetix.tech
CONTACT_RATE_LIMIT_WINDOW_SECONDS=600
CONTACT_RATE_LIMIT_MAX_REQUESTS=5

# Optional SMTP
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
CONTACT_ALERT_TO=

## Step 3: Register systemd service
- Copy `deploy/aponetix.service` to `/etc/systemd/system/aponetix.service`
- Then:
  - `sudo systemctl daemon-reload`
  - `sudo systemctl enable aponetix`
  - `sudo systemctl start aponetix`

## Step 4: Configure Nginx
- Copy `deploy/nginx-aponetix.conf` to `/etc/nginx/sites-available/aponetix`
- Enable:
  - `sudo ln -s /etc/nginx/sites-available/aponetix /etc/nginx/sites-enabled/aponetix`
- Test and reload:
  - `sudo nginx -t`
  - `sudo systemctl reload nginx`

## Step 5: GitHub Actions secrets
In GitHub repo settings -> Secrets and variables -> Actions, add:
- `ORIGIN_HOST` (server IP)
- `ORIGIN_USER` (SSH user)
- `ORIGIN_SSH_KEY` (private key)
- `ORIGIN_SSH_PORT` (usually 22)

## Step 6: Cloudflare DNS + SSL
In Cloudflare for your domain:
1. Add `A` record:
   - Name: `@`
   - IPv4: your origin server IP
   - Proxy: ON (orange cloud)
2. Add `CNAME`:
   - Name: `www`
   - Target: `aponetix.tech`
   - Proxy: ON
3. SSL/TLS mode: `Full (strict)`
4. Enable:
   - Always Use HTTPS
   - Automatic HTTPS Rewrites

## Step 7: First deploy
- Push to `main` branch
- GitHub Action `Deploy APONETIX to Origin` will run
- Validate:
  - `https://aponetix.tech/health`
  - `https://aponetix.tech/ready`

## Important Note
Cloudflare Pages is for static/Jamstack style; this Flask app should use origin deployment + Cloudflare proxy.
