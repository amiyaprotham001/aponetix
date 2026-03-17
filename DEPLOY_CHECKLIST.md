# APONETIX 100% Launch Checklist

## 1) Server Readiness
- [ ] Python environment created and dependencies installed
- [ ] `waitress` run command tested
- [ ] Firewall open for origin app port

## 2) Environment Configuration
- [ ] `.env` values configured from `.env.example`
- [ ] `APP_ENV=production`
- [ ] Strong `FLASK_SECRET_KEY` set
- [ ] `SESSION_COOKIE_SECURE=1`
- [ ] `TRUST_PROXY=1` (Cloudflare proxied setup)

## 3) Cloudflare Setup
- [ ] DNS record (A/CNAME) points to origin
- [ ] Proxy enabled (orange cloud)
- [ ] SSL/TLS mode set to `Full (strict)`
- [ ] Always Use HTTPS enabled
- [ ] Automatic HTTPS Rewrites enabled

## 4) App Verification
- [ ] `/health` returns OK
- [ ] `/ready` returns ready status
- [ ] `/robots.txt` accessible
- [ ] `/sitemap.xml` accessible
- [ ] `/.well-known/security.txt` accessible
- [ ] Contact form submission works
- [ ] `predeploy_check.py` passes

## 5) Security Verification
- [ ] Response headers include CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- [ ] CSRF protection blocks invalid tokens
- [ ] Rate limit blocks excessive submissions
- [ ] Logs written to `logs/app.log`

## 6) Data and Backup
- [ ] `data/contact_submissions.db` is being written correctly
- [ ] Backup policy for `data/` and `logs/` set

## 7) Final Business Checks
- [ ] Emails and social links are correct
- [ ] Privacy/Terms reviewed and approved
- [ ] Brand content approved by founder

When all boxes are checked, deployment is launch-ready.
