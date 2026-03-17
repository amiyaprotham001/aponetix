# APONETIX Website

International-style professional brand website for APONETIX, built with Flask and modern HTML/CSS.

## Brand Summary
- Brand Name: APONETIX
- Type: Technology and digital engineering brand website
- Unofficial Launch Date: January 12, 2026
- Official Emails: info@aponetix.tech, support@aponetix.tech

## Included Pages
- `/` — Homepage
- `/privacy` — Privacy Policy
- `/terms` — Terms & Conditions
- `/health` — Lightweight service health endpoint
- `/ready` — Readiness endpoint for load balancer/process checks
- `/robots.txt` — Search crawler directives
- `/sitemap.xml` — XML sitemap
- `/.well-known/security.txt` — Security contact policy

## Contact Submission Flow
- Homepage contact form submits to `/contact` via `POST`
- Basic anti-spam honeypot is enabled
- CSRF token validation is enabled
- In-memory rate limit is enabled for contact endpoint
- Submissions are stored in `data/contact_submissions.db` (SQLite)
- Success/error feedback is shown on homepage

## Environment Variables
- `FLASK_SECRET_KEY` — required for stable session security across restarts
- `FLASK_DEBUG` — set `1` only for local debugging
- `CONTACT_RATE_LIMIT_WINDOW_SECONDS` — default `600`
- `CONTACT_RATE_LIMIT_MAX_REQUESTS` — default `5`
- `SESSION_COOKIE_SECURE` — set `1` in HTTPS production
- `APP_ENV` — set `production` for strict production safety checks
- `TRUST_PROXY` — set `1` only when behind Cloudflare/reverse proxy (default `0`)
- `SITE_URL` — optional canonical base URL (example: `https://aponetix.tech`) for sitemap/robots generation
- `ALLOWED_HOSTS` — comma-separated allowed hostnames for host-header protection

### Optional Email Alert (Contact Notification)
- `SMTP_HOST`
- `SMTP_PORT` (default `587`)
- `SMTP_USER`
- `SMTP_PASSWORD`
- `CONTACT_ALERT_TO`

If SMTP variables are set, contact submissions can trigger email notifications.

## Local Development
1. Open terminal in project folder:
   ```bash
   cd d:\web
   ```
2. Create and activate virtual environment (recommended):
   ```bash
   C:/Users/amiya/AppData/Local/Programs/Python/Python314/python.exe -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   C:/Users/amiya/AppData/Local/Programs/Python/Python314/python.exe -m pip install -r requirements.txt
   ```
4. Run application:
   ```bash
   C:/Users/amiya/AppData/Local/Programs/Python/Python314/python.exe app.py
   ```
5. Open in browser:
   ```
   http://127.0.0.1:5000
   ```

## Debug Mode
Debug mode is disabled by default.

- Enable debug (PowerShell):
  ```powershell
  $env:FLASK_DEBUG="1"
  C:/Users/amiya/AppData/Local/Programs/Python/Python314/python.exe app.py
  ```

## Production Note
For production deployment, run behind a production WSGI server and reverse proxy, keep `FLASK_DEBUG` disabled, and configure domain SSL.

Strict production requirements:
- `APP_ENV=production` requires `FLASK_SECRET_KEY`, `SITE_URL`, and `ALLOWED_HOSTS`

### Recommended Run Command (Production)
```bash
waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
```

Alternative artifacts included:
- `Procfile` for platform process managers
- `start.ps1` for Windows startup using `.env`

## Cloudflare Deployment (Practical Path)
Cloudflare does not host Flask apps directly like static pages. Use this model:

1. Deploy this Flask app to an origin server (VPS/VM/container) with `waitress`.
2. Point your domain DNS in Cloudflare to that origin (proxied `A`/`CNAME` record).
3. Enable SSL/TLS in Cloudflare (`Full (strict)` recommended).
4. Set required env vars on origin (`FLASK_SECRET_KEY`, `SESSION_COOKIE_SECURE=1`, SMTP values if needed).
5. Keep Cloudflare proxy enabled for caching, WAF, and DDoS protection.

Optional advanced: use Cloudflare Tunnel to avoid exposing direct origin IP.

## Predeploy Validation (Recommended)
Run before going live:

```bash
C:/Users/amiya/AppData/Local/Programs/Python/Python314/python.exe predeploy_check.py
```

This validates required env values and deployment-critical files.

## Security Baseline Included
- Security headers (`CSP`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`)
- HSTS header on secure HTTPS requests
- Proxy-safe IP handling (Cloudflare compatible)
- Custom `404` and `500` error pages
- CSRF validation for contact form
- Basic in-memory rate limiting for form abuse control
- Rotating application logs to `logs/app.log`

## Data Notes
- Contact submissions are written to SQLite (`data/contact_submissions.db`)
- SQLite is configured with WAL mode for better write reliability
- Ensure regular backup of `data/` for production reliability

Production behavior note:
- When `APP_ENV=production`, secure session cookies are enforced automatically.
