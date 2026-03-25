#!/usr/bin/env python3
"""
Deployment verification script for APONETIX on Render
Run this locally before deploying to ensure everything is configured correctly
"""

import os
import sys
import secrets
from pathlib import Path

def check_requirements():
    """Check if all required packages are in requirements.txt"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    with open(req_file) as f:
        content = f.read()
    
    required = ["Flask", "waitress"]
    missing = [pkg for pkg in required if pkg.lower() not in content.lower()]
    
    if missing:
        print(f"❌ Missing packages in requirements.txt: {missing}")
        return False
    
    print("✅ requirements.txt looks good")
    return True

def check_env_vars():
    """Check if critical environment variables are set"""
    critical_vars = [
        "FLASK_SECRET_KEY",
        "SITE_URL",
        "ALLOWED_HOSTS",
        "APP_ENV"
    ]
    
    missing = [var for var in critical_vars if not os.getenv(var)]
    
    if missing:
        print(f"⚠️  Missing environment variables: {missing}")
        print("   These MUST be set in Render dashboard before deploying")
        return False
    
    print("✅ All critical environment variables are set")
    return True

def check_flask_secret_key():
    """Verify Flask secret key is strong"""
    secret = os.getenv("FLASK_SECRET_KEY", "")
    
    if not secret:
        print("⚠️  FLASK_SECRET_KEY not set")
        print("   Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
        return False
    
    if len(secret) < 32:
        print(f"❌ FLASK_SECRET_KEY too short ({len(secret)} chars, need 64+ hex chars)")
        return False
    
    print(f"✅ FLASK_SECRET_KEY looks strong ({len(secret)} chars)")
    return True

def check_app_config():
    """Check if app.py has production configurations"""
    app_file = Path("app.py")
    if not app_file.exists():
        print("❌ app.py not found")
        return False
    
    with open(app_file) as f:
        content = f.read()
    
    checks = [
        ("CSRF protection", "csrf_token" in content),
        ("Rate limiting", "is_rate_limited" in content),
        ("Logging", "logger" in content),
        ("Security headers", "X-Content-Type-Options" in content),
        ("Database support", "sqlite3" in content),
    ]
    
    all_good = True
    for name, present in checks:
        symbol = "✅" if present else "❌"
        print(f"{symbol} {name}: {'Present' if present else 'Missing'}")
        if not present:
            all_good = False
    
    return all_good

def check_templates():
    """Check if templates exist"""
    templates_dir = Path("templates")
    if not templates_dir.exists():
        print("❌ templates/ directory not found")
        return False
    
    required_templates = ["index.html", "404.html", "500.html"]
    missing = [t for t in required_templates if not (templates_dir / t).exists()]
    
    if missing:
        print(f"❌ Missing templates: {missing}")
        return False
    
    print(f"✅ All required templates found")
    return True

def check_wsgi():
    """Check if wsgi.py is correctly configured"""
    wsgi_file = Path("wsgi.py")
    if not wsgi_file.exists():
        print("❌ wsgi.py not found")
        return False
    
    with open(wsgi_file) as f:
        content = f.read()
    
    if "from app import app" not in content:
        print("❌ wsgi.py doesn't import app correctly")
        return False
    
    print("✅ wsgi.py is correctly configured")
    return True

def suggest_secret_key():
    """Suggest a strong secret key"""
    print("\n" + "="*60)
    print("SUGGESTED FLASK_SECRET_KEY for Render:")
    print("="*60)
    key = secrets.token_hex(32)
    print(f"\n{key}\n")
    print("Copy this to Render Dashboard → Environment Variables")
    print("="*60 + "\n")

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("APONETIX - Render Deployment Verification")
    print("="*60 + "\n")
    
    checks = [
        ("Requirements", check_requirements),
        ("Flask Configuration", check_app_config),
        ("Templates", check_templates),
        ("WSGI Setup", check_wsgi),
        ("Environment Variables", check_env_vars),
        ("Flask Secret Key", check_flask_secret_key),
    ]
    
    results = []
    for name, check_fn in checks:
        print(f"\n📋 Checking {name}...")
        try:
            result = check_fn()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error during check: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, result in results:
        symbol = "✅" if result else "⚠️ "
        print(f"{symbol} {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All checks passed! Ready to deploy to Render.")
    else:
        print("\n⚠️  Some checks failed. Review and fix before deploying.")
    
    suggest_secret_key()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
