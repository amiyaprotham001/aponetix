# Render Deployment Guide for APONETIX

## Prerequisites
- GitHub account with your `aponetix` repository pushed
- Render account (sign up at https://render.com)

## Step-by-Step Deployment

### 1. Connect GitHub Repository to Render
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Select **"Connect account"** and authorize GitHub
4. Select your **`aponetix`** repository
5. Click **"Connect"**

### 2. Configure Service (if not using render.yaml)
**Web Service Settings:**
- **Name**: `aponetix`
- **Environment**: `Python 3`
- **Region**: `Oregon` (or your preferred)
- **Plan**: `Starter` (free tier available)

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `waitress-serve --host=0.0.0.0 --port=$PORT wsgi:app`

**Auto-deploy**: Enable "Auto-deploy new commits"

### 3. Add Environment Variables in Render Dashboard
After creating the service, go to **Settings** → **Environment** and add:

| Variable | Value | Notes |
|----------|-------|-------|
| `FLASK_ENV` | `production` | Required |
| `APP_ENV` | `production` | Enables strict validation |
| `SESSION_COOKIE_SECURE` | `1` | HTTPS only cookies |
| `TRUST_PROXY` | `1` | For Render proxy headers |
| `FLASK_SECRET_KEY` | *(generate strong key)* | **IMPORTANT**: Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SITE_URL` | `https://aponetix.onrender.com` | Replace with your actual domain |
| `ALLOWED_HOSTS` | `aponetix.onrender.com` | Allow Render domain |

**For Email Notifications (optional):**
- `SMTP_HOST`: Your SMTP server (e.g., `smtp.gmail.com`)
- `SMTP_PORT`: `587`
- `SMTP_USER`: Your email
- `SMTP_PASSWORD`: App-specific password (not regular password)
- `CONTACT_ALERT_TO`: Email to receive contact submissions

### 4. Configure Persistent Disk (for SQLite database)
1. Go to **Disks** section in service settings
2. Click **"Create Disk"**
3. **Mount Path**: `/opt/render/project/data`
4. **Size**: `1 GB` (enough for contact submissions)
5. Update `DATA_DIR` path in code if needed (it's already set to `./data`)

### 5. Generate Strong Secret Key
Run this locally to generate a secure key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste in Render dashboard as `FLASK_SECRET_KEY`

### 6. Deploy
1. Click **"Deploy latest commit"** button
2. Watch the logs to confirm successful deployment
3. Access your site at: `https://aponetix.onrender.com`

---

## Post-Deployment Verification

### Health Check
```bash
curl https://aponetix.onrender.com/health
```
Should return: `{"status": "ok"}`

### Readiness Check
```bash
curl https://aponetix.onrender.com/ready
```

### Robot Check
```bash
curl https://aponetix.onrender.com/robots.txt
```

### Test Contact Form
Visit homepage and submit test contact form to ensure database writes work.

---

## Troubleshooting

### "FLASK_SECRET_KEY is required" Error
- Go to Render dashboard → Environment → Add `FLASK_SECRET_KEY` variable
- Must be long & random (generate with `secrets.token_hex(32)`)

### "SITE_URL is required"
- Add `SITE_URL` = `https://aponetix.onrender.com` (or your custom domain)

### "ALLOWED_HOSTS is required"
- Add `ALLOWED_HOSTS` = `aponetix.onrender.com` (or your custom domain)

### Database Not Persisting
- Ensure Disk is mounted at `/opt/render/project/data`
- Check that `DATA_DIR = Path(__file__).parent / "data"` in app.py is using relative path

### 500 Error on Form Submission
- Check logs: Dashboard → Service → Logs
- Verify `FLASK_SECRET_KEY` is set (not empty)
- Verify disk is properly mounted

### Slow Initial Load
- Render free tier may have startup delays
- First request after inactivity can take 30+ seconds
- Consider upgrading plan for faster performance

---

## Custom Domain Setup

1. Go to Render Dashboard → Service Settings
2. Add your custom domain (e.g., `aponetix.tech`)
3. Follow DNS instructions in Render dashboard
4. Update `SITE_URL` and `ALLOWED_HOSTS` env vars with your domain
5. Wait for DNS propagation (can take 24-48 hours)

---

## Automatic Redeploys

Render watches your GitHub repository. Any push to `main` branch will trigger automatic redeploy if enabled.

To disable: Service Settings → Toggle off "Auto-deploy new commits"

---

## Monitor Live Logs
```
Go to Dashboard → Service → Logs to see real-time activity
```

---

**Questions?** Check Render docs: https://render.com/docs
