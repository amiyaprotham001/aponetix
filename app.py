import os
import re
import secrets
import logging
import smtplib
import sqlite3
from collections import defaultdict, deque
from datetime import datetime, timezone
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, abort, flash, g, make_response, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

app_env = os.getenv("APP_ENV", "development").lower()
trust_proxy = os.getenv("TRUST_PROXY", "0") == "1"
site_url = os.getenv("SITE_URL", "").strip().rstrip("/")
allowed_hosts_raw = os.getenv("ALLOWED_HOSTS", "")
allowed_hosts = {host.strip().lower() for host in allowed_hosts_raw.split(",") if host.strip()}
if app_env == "production" and not os.getenv("FLASK_SECRET_KEY"):
    raise RuntimeError("FLASK_SECRET_KEY is required when APP_ENV=production")

if app_env == "production" and not site_url:
    raise RuntimeError("SITE_URL is required when APP_ENV=production")

if app_env == "production" and not allowed_hosts:
    raise RuntimeError("ALLOWED_HOSTS is required when APP_ENV=production")

if app_env == "production":
    app.config["SESSION_COOKIE_SECURE"] = True

if trust_proxy:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CONTACT_DB = DATA_DIR / "contact_submissions.db"

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logger = logging.getLogger("aponetix")
logger.setLevel(logging.INFO)
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

if not os.getenv("FLASK_SECRET_KEY"):
    logger.warning("FLASK_SECRET_KEY not set. Using development fallback key.")

CONTACT_WINDOW_SECONDS = int(os.getenv("CONTACT_RATE_LIMIT_WINDOW_SECONDS", "600"))
CONTACT_MAX_REQUESTS = int(os.getenv("CONTACT_RATE_LIMIT_MAX_REQUESTS", "5"))
RATE_LIMIT_STORE = defaultdict(deque)


def init_contact_db():
    with sqlite3.connect(CONTACT_DB, timeout=10) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_contact_submissions_timestamp ON contact_submissions(timestamp_utc)"
        )
        conn.commit()


init_contact_db()


def is_valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def sanitize_csv_text(value):
    cleaned = value.replace("\r", " ").replace("\n", " ").strip()
    if cleaned.startswith(("=", "+", "-", "@")):
        cleaned = "'" + cleaned
    return cleaned


def get_db_connection():
    connection = sqlite3.connect(CONTACT_DB, timeout=10)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection


def get_public_base_url():
    if site_url.startswith("https://") or site_url.startswith("http://"):
        return site_url
    scheme = "https" if request.is_secure else "http"
    return f"{scheme}://{request.host}"


@app.before_request
def before_request_security():
    g.csp_nonce = secrets.token_urlsafe(16)

    if allowed_hosts:
        request_host = request.host.split(":")[0].lower()
        if request_host not in allowed_hosts:
            logger.warning("Blocked host header: %s", request.host)
            abort(400)


def get_client_ip():
    cloudflare_ip = request.headers.get("CF-Connecting-IP", "").strip()
    if trust_proxy and cloudflare_ip:
        return cloudflare_ip

    forwarded_for = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded_for and trust_proxy:
        return forwarded_for.split(",")[0].strip()

    return request.remote_addr or "unknown"


def is_rate_limited(ip_address):
    current_time = datetime.now(timezone.utc).timestamp()

    if len(RATE_LIMIT_STORE) > 10_000:
        stale_keys = []
        for key, queue in RATE_LIMIT_STORE.items():
            while queue and current_time - queue[0] > CONTACT_WINDOW_SECONDS:
                queue.popleft()
            if not queue:
                stale_keys.append(key)
        for key in stale_keys:
            RATE_LIMIT_STORE.pop(key, None)

    requests_queue = RATE_LIMIT_STORE[ip_address]

    while requests_queue and current_time - requests_queue[0] > CONTACT_WINDOW_SECONDS:
        requests_queue.popleft()

    if len(requests_queue) >= CONTACT_MAX_REQUESTS:
        return True

    requests_queue.append(current_time)
    return False


def send_contact_email(name, email, message, timestamp):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    alert_to = os.getenv("CONTACT_ALERT_TO")

    if not all([smtp_host, smtp_user, smtp_password, alert_to]):
        return

    email_message = EmailMessage()
    email_message["Subject"] = "New APONETIX Contact Submission"
    email_message["From"] = smtp_user
    email_message["To"] = alert_to
    email_message.set_content(
        f"Timestamp (UTC): {timestamp}\n"
        f"Name: {name}\n"
        f"Email: {email}\n\n"
        f"Message:\n{message}\n"
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp_server:
        smtp_server.starttls()
        smtp_server.login(smtp_user, smtp_password)
        smtp_server.send_message(email_message)


def generate_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def csrf_context_processor():
    return {
        "csrf_token": generate_csrf_token,
        "csp_nonce": lambda: getattr(g, "csp_nonce", ""),
    }


@app.after_request
def apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    nonce = getattr(g, "csp_nonce", "")
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Origin-Agent-Cluster"] = "?1"
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    return response


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contact", methods=["POST"])
def contact():
    ip_address = get_client_ip()
    if is_rate_limited(ip_address):
        flash("Too many requests. Please try again after a few minutes.", "error")
        logger.warning("Rate limit triggered for IP %s", ip_address)
        return redirect(url_for("home") + "#contact")

    form_token = request.form.get("csrf_token", "")
    session_token = session.get("csrf_token", "")
    if not form_token or not session_token or not secrets.compare_digest(form_token, session_token):
        flash("Invalid session token. Please try again.", "error")
        logger.warning("CSRF validation failed for IP %s", ip_address)
        return redirect(url_for("home") + "#contact")

    honeypot = request.form.get("website", "").strip()
    if honeypot:
        flash("Submission blocked.", "error")
        logger.warning("Honeypot triggered for IP %s", ip_address)
        return redirect(url_for("home") + "#contact")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    message = request.form.get("message", "").strip()

    if len(name) < 2:
        flash("Please provide a valid name.", "error")
        return redirect(url_for("home") + "#contact")

    if len(name) > 120:
        flash("Name is too long.", "error")
        return redirect(url_for("home") + "#contact")

    if not is_valid_email(email):
        flash("Please provide a valid email address.", "error")
        return redirect(url_for("home") + "#contact")

    if len(email) > 254:
        flash("Email is too long.", "error")
        return redirect(url_for("home") + "#contact")

    if len(message) < 10:
        flash("Please provide a brief project message.", "error")
        return redirect(url_for("home") + "#contact")

    if len(message) > 3000:
        flash("Message is too long.", "error")
        return redirect(url_for("home") + "#contact")

    safe_name = sanitize_csv_text(name)
    safe_email = sanitize_csv_text(email)
    safe_message = sanitize_csv_text(message)

    timestamp = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO contact_submissions(timestamp_utc, name, email, message) VALUES (?, ?, ?, ?)",
            (timestamp, safe_name, safe_email, safe_message),
        )
        conn.commit()

    try:
        send_contact_email(name=safe_name, email=safe_email, message=safe_message, timestamp=timestamp)
    except Exception:
        logger.exception("Failed to send contact alert email")

    session["csrf_token"] = secrets.token_urlsafe(32)
    logger.info("Contact submission saved for %s", email)

    flash("Thanks. Your message was submitted successfully.", "success")
    return redirect(url_for("home") + "#contact")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/health")
def health():
    db_ok = True
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return {"status": "ok" if db_ok else "degraded", "service": "aponetix-web", "db": db_ok}, status_code


@app.route("/ready")
def ready():
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
    except Exception:
        return {"ready": False}, 503
    return {"ready": True}, 200


@app.route("/.well-known/security.txt")
def security_txt():
    content = (
        "Contact: mailto:ceo@aponetix.com\n"
        "Contact: mailto:support@aponetix.tech\n"
        "Policy: /privacy\n"
        "Preferred-Languages: en\n"
    )
    response = make_response(content)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response


@app.route("/robots.txt")
def robots():
    base_url = get_public_base_url()
    content = f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n"
    response = make_response(content)
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response


@app.route("/sitemap.xml")
def sitemap():
    base_url = get_public_base_url()
    urls = [
        f"{base_url}/",
        f"{base_url}/privacy",
        f"{base_url}/terms",
    ]
    body = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
    xml = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">{body}</urlset>"
    response = make_response(xml)
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


@app.errorhandler(413)
def payload_too_large(error):
    return make_response("Payload too large", 413)


@app.errorhandler(405)
def method_not_allowed(error):
    return make_response("Method not allowed", 405)


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
