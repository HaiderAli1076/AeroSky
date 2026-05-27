from waitress import serve
from app import app
import logging
import sys

logger = logging.getLogger("weather_logger")

if __name__ == "__main__":
    logger.info("Starting Waitress production server on port 8080...")
    print("--------------------------------------------------")
    print("AeroSky Production Server Started")
    print("Serving AeroSky Dashboard on http://localhost:8080")
    print("Press Ctrl+C to terminate.")
    print("--------------------------------------------------")
    
    try:
        serve(app, host="0.0.0.0", port=8080, threads=4)
    except Exception as e:
        logger.error(f"Waitress server failed to start: {e}")
        print(f"CRITICAL: Failed to launch Waitress server: {e}", file=sys.stderr)
        sys.exit(1)
