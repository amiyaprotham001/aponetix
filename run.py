import os
import logging
from waitress import serve
from app import app

if __name__ == "__main__":
    # Render environment provides PORT
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Waitress production server on port {port}...")
    serve(app, host="0.0.0.0", port=port)