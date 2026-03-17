import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ENV_PATH = ROOT / ".env"

REQUIRED_IN_PROD = [
    "APP_ENV",
    "FLASK_SECRET_KEY",
    "SESSION_COOKIE_SECURE",
    "TRUST_PROXY",
    "SITE_URL",
    "ALLOWED_HOSTS",
]


def load_env_file(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def fail(message: str):
    print(f"[FAIL] {message}")
    return False


def ok(message: str):
    print(f"[OK] {message}")
    return True


def validate():
    passed = True
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env != "production":
        return fail("APP_ENV must be set to 'production' for predeploy check")
    ok("APP_ENV is production")

    for key in REQUIRED_IN_PROD:
        if not os.getenv(key):
            passed = fail(f"Missing required env var: {key}") and passed
        else:
            ok(f"{key} is set")

    secret = os.getenv("FLASK_SECRET_KEY", "")
    if len(secret) < 32:
        passed = fail("FLASK_SECRET_KEY should be at least 32 characters") and passed
    else:
        ok("FLASK_SECRET_KEY length looks good")

    if os.getenv("SESSION_COOKIE_SECURE") != "1":
        passed = fail("SESSION_COOKIE_SECURE must be 1 in production") and passed
    else:
        ok("SESSION_COOKIE_SECURE is set to 1")

    if os.getenv("TRUST_PROXY") != "1":
        passed = fail("TRUST_PROXY must be 1 behind Cloudflare") and passed
    else:
        ok("TRUST_PROXY is set to 1")

    site_url = os.getenv("SITE_URL", "")
    if not re.match(r"^https://", site_url):
        passed = fail("SITE_URL must start with https://") and passed
    else:
        ok("SITE_URL format is valid")

    hosts = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
    if not hosts:
        passed = fail("ALLOWED_HOSTS must contain at least one hostname") and passed
    else:
        ok("ALLOWED_HOSTS has entries")

    if not (ROOT / "wsgi.py").exists():
        passed = fail("wsgi.py not found") and passed
    else:
        ok("wsgi.py exists")

    if not (ROOT / "templates" / "index.html").exists():
        passed = fail("templates/index.html not found") and passed
    else:
        ok("templates/index.html exists")

    return passed


def main():
    load_env_file(ENV_PATH)
    success = validate()
    if success:
        print("\nPredeploy check passed.")
        sys.exit(0)
    print("\nPredeploy check failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
