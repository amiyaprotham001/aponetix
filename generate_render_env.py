#!/usr/bin/env python3
"""
Generate secure environment variables for APONETIX Render deployment
"""

import secrets
import subprocess
from datetime import datetime

def generate_flask_secret_key():
    """Generate a strong Flask secret key"""
    return secrets.token_hex(32)

def get_hostname_from_git():
    """Try to get repository URL from git"""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None

def main():
    print("\n" + "="*70)
    print("APONETIX - Render Environment Variables Generator")
    print("="*70 + "\n")
    
    # Generate Flask secret key
    secret_key = generate_flask_secret_key()
    print("🔐 Generated FLASK_SECRET_KEY (strong, random):")
    print(f"   {secret_key}\n")
    
    # Get domain/URL
    print("📍 Render Domain Information:")
    print("   Default Render domain: https://aponetix.onrender.com")
    print("   (or your custom domain if configured)\n")
    
    # Suggest environment variables
    print("📝 Copy these to Render Dashboard → Environment Variables:")
    print("="*70)
    
    env_vars = {
        "FLASK_ENV": "production",
        "APP_ENV": "production",
        "SESSION_COOKIE_SECURE": "1",
        "TRUST_PROXY": "1",
        "FLASK_SECRET_KEY": secret_key,
        "SITE_URL": "https://aponetix.onrender.com",
        "ALLOWED_HOSTS": "aponetix.onrender.com",
    }
    
    print("\n# Copy all these:")
    for key, value in env_vars.items():
        print(f"{key}={value}")
    
    print("\n" + "="*70)
    print("📧 OPTIONAL - For Email Notifications:")
    print("="*70)
    print("""
If you want to receive email notifications for contact submissions:

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
CONTACT_ALERT_TO=your-email@gmail.com

Note: Use Gmail App Password, not your regular password
Generate at: https://myaccount.google.com/apppasswords
    """)
    
    print("\n" + "="*70)
    print("📋 Next Steps:")
    print("="*70)
    print("""
1. Go to https://dashboard.render.com
2. Create new Web Service or select existing
3. Add all environment variables from above
4. Set "Build Command": pip install -r requirements.txt
5. Set "Start Command": waitress-serve --host=0.0.0.0 --port=$PORT wsgi:app
6. Create a Disk mounted at: /opt/render/project/data (1GB)
7. Deploy and test!
    """)
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
