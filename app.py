import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone, timedelta
import httpx
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv

# Import database module
import db

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Configure logging with rotation (max 1MB, 5 backups)
logger = logging.getLogger("weather_logger")
logger.setLevel(logging.INFO)
# Prevent duplicate handlers if app.py is re-imported
if not logger.handlers:
    file_handler = RotatingFileHandler("weather.log", maxBytes=1024*1024, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Verify API key is set - if missing, exit with clear error
if not API_KEY:
    logger.error("Startup failed: OPENWEATHER_API_KEY environment variable is not set.")
    print("CRITICAL Startup Error: OPENWEATHER_API_KEY environment variable is not set.", file=sys.stderr)
    print("Please configure your API key in the .env file.", file=sys.stderr)
    sys.exit(1)

# Initialize database
try:
    db.init_db()
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    print(f"CRITICAL: Failed to initialize database: {e}", file=sys.stderr)
    sys.exit(1)

app = Flask(__name__)

# In-memory cache dictionary: key -> {"data": data, "timestamp": timestamp}
cache = {}
CACHE_TTL = 600  # 10 minutes

def sanitize_city(city: str) -> bool:
    """
    Returns True if valid, False if it contains forbidden characters or is too long.
    Forbidden: < > & ; ' " ( )
    Max length: 100
    """
    if not city or len(city) > 100:
        return False
    forbidden = ["<", ">", "&", ";", "'", '"', "(", ")"]
    for char in forbidden:
        if char in city:
            return False
    return True

def fetch_with_retry(url: str, client: httpx.Client) -> httpx.Response:
    """
    Fetches the URL using the provided HTTPX client, retrying with exponential backoff.
    Retries up to 3 times (delays 1s, 2s, 4s).
    """
    delays = [1.0, 2.0, 4.0]
    for attempt, delay in enumerate(delays):
        try:
            response = client.get(url)
            # Check for invalid OWM key immediately
            if response.status_code == 401:
                raise httpx.HTTPStatusError("Unauthorized key", request=response.request, response=response)
            # Check for rate limiting — no point retrying immediately
            if response.status_code == 429:
                raise httpx.HTTPStatusError("Rate limit exceeded", request=response.request, response=response)
            response.raise_for_status()
            return response
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            # For 401/404/429, we know they won't succeed on retry, raise immediately
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code in [401, 404, 429]:
                    raise e
            
            # If we have attempts left, wait and retry
            if attempt < len(delays) - 1:
                logger.warning(f"API request failed: {e}. Retrying in {delay}s (Attempt {attempt + 1}/3)...")
                time.sleep(delay)
            else:
                logger.error(f"API request failed after {len(delays)} attempts: {e}")
                raise e

def resolve_city_coords(city: str) -> dict:
    """
    Resolves city name to coordinates. Checks cache first to avoid redundant API hits.
    """
    city_normalized = city.lower().strip()
    geo_cache_key = f"geo_{city_normalized}"
    now = time.time()
    
    if geo_cache_key in cache:
        geo_entry = cache[geo_cache_key]
        if now - geo_entry["timestamp"] < CACHE_TTL:
            logger.info(f"Geo cache HIT for city: '{city_normalized}'")
            return geo_entry["data"]
            
    # Fetch from OWM geocoding API
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    with httpx.Client(timeout=5.0) as client:
        geo_response = fetch_with_retry(geo_url, client)
        geo_data = geo_response.json()
        
        if not geo_data:
            raise ValueError(f"City '{city}' not found.")
            
        location = geo_data[0]
        result = {
            "lat": location.get("lat"),
            "lon": location.get("lon"),
            "city": location.get("name"),
            "country": location.get("country")
        }
        
        cache[geo_cache_key] = {
            "data": result,
            "timestamp": now
        }
        logger.info(f"Geo cache saved for city: '{city_normalized}'")
        return result

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/weather")
def get_weather():
    city = request.args.get("city", "").strip()
    
    # Sanitization
    if not city or not sanitize_city(city):
        logger.error(f"Invalid input city name: '{city}'")
        return jsonify({"error": "Bad request: invalid city name format or length."}), 400
        
    city_normalized = city.lower()
    now = time.time()
    weather_cache_key = f"weather_{city_normalized}"
    
    # 1. Check in-memory cache
    if weather_cache_key in cache:
        cache_entry = cache[weather_cache_key]
        # Check if fresh (TTL < 600s)
        if now - cache_entry["timestamp"] < CACHE_TTL:
            logger.info(f"Weather cache HIT for city: '{city_normalized}'")
            return jsonify(cache_entry["data"])
        else:
            logger.info(f"Weather cache expired (stale) for city: '{city_normalized}'")
            
    # 2. Call API with retries
    try:
        coords = resolve_city_coords(city)
        lat = coords["lat"]
        lon = coords["lon"]
        actual_city = coords["city"]
        country = coords["country"]
        
        # Call Current Weather API
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}"
        
        with httpx.Client(timeout=5.0) as client:
            weather_response = fetch_with_retry(weather_url, client)
            weather_data = weather_response.json()
            
            # Extract fields
            main_data = weather_data.get("main", {})
            temp_k = main_data.get("temp")
            feels_like_k = main_data.get("feels_like")
            humidity = main_data.get("humidity")
            pressure = main_data.get("pressure")
            
            wind_speed = weather_data.get("wind", {}).get("speed")
            
            weather_list = weather_data.get("weather", [])
            condition = ""
            icon_code = ""
            if weather_list:
                condition = weather_list[0].get("description", "")
                icon_code = weather_list[0].get("icon", "")
                
            icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png" if icon_code else ""
            
            response_payload = {
                "city": actual_city,
                "country": country,
                "temp_k": int(round(temp_k)) if temp_k is not None else None,
                "feels_like_k": int(round(feels_like_k)) if feels_like_k is not None else None,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "pressure": pressure,
                "condition": condition.capitalize() if condition else "",
                "icon_url": icon_url
            }
            
            # Cache the successful response
            cache[weather_cache_key] = {
                "data": response_payload,
                "timestamp": now
            }
            
            logger.info(f"Successful Current Weather API call for city: '{city_normalized}'")
            return jsonify(response_payload)
            
    except Exception as e:
        # 3. Stale-data fallback
        if weather_cache_key in cache:
            cache_entry = cache[weather_cache_key]
            stale_minutes = int(round((now - cache_entry["timestamp"]) / 60.0))
            
            # Return stale data with stale banner indicators
            stale_payload = dict(cache_entry["data"])
            stale_payload["stale"] = True
            stale_payload["stale_minutes"] = stale_minutes
            
            logger.warning(f"Weather API failed, serving stale cache data for: '{city_normalized}' (stale by {stale_minutes} minutes)")
            return jsonify(stale_payload)
            
        # If cache doesn't exist, handle the error gracefully
        logger.error(f"Weather API failed and no cache exists for: '{city_normalized}'. Error: {e}")
        
        # Map OWM exceptions to frontend friendly responses
        if isinstance(e, ValueError) and "not found" in str(e):
            return jsonify({"error": f"City '{city}' not found."}), 404
            
        if isinstance(e, httpx.HTTPStatusError):
            status_code = e.response.status_code
            if status_code == 401:
                return jsonify({"error": "Service Unavailable: Check OWM API key."}), 503
            elif status_code == 404:
                return jsonify({"error": "City weather data not found."}), 404
                
        # If it was a timeout
        if isinstance(e, httpx.TimeoutException):
            return jsonify({"error": "Gateway Timeout: OpenWeatherMap API did not respond in time."}), 504
            
        return jsonify({"error": "Service Unavailable: Check your internet connection."}), 503

@app.route("/forecast")
def get_forecast():
    city = request.args.get("city", "").strip()
    
    # Sanitization
    if not city or not sanitize_city(city):
        logger.error(f"Invalid input city name for forecast: '{city}'")
        return jsonify({"error": "Bad request: invalid city name format or length."}), 400
        
    city_normalized = city.lower()
    now = time.time()
    forecast_cache_key = f"forecast_{city_normalized}"
    
    # 1. Check in-memory cache
    if forecast_cache_key in cache:
        cache_entry = cache[forecast_cache_key]
        # Check if fresh (TTL < 600s)
        if now - cache_entry["timestamp"] < CACHE_TTL:
            logger.info(f"Forecast cache HIT for city: '{city_normalized}'")
            return jsonify(cache_entry["data"])
        else:
            logger.info(f"Forecast cache expired (stale) for city: '{city_normalized}'")
            
    # 2. Call API with retries
    try:
        coords = resolve_city_coords(city)
        lat = coords["lat"]
        lon = coords["lon"]
        
        # Call 5-Day Forecast API
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
        
        with httpx.Client(timeout=5.0) as client:
            forecast_response = fetch_with_retry(forecast_url, client)
            forecast_data = forecast_response.json()
            
            timezone_offset = forecast_data.get("city", {}).get("timezone", 0)
            tz = timezone(timedelta(seconds=timezone_offset))
            
            # Group the 3-hour entries by local timezone date
            grouped_entries = {}
            for entry in forecast_data.get("list", []):
                dt_val = datetime.fromtimestamp(entry["dt"], tz=tz)
                day_str = dt_val.strftime("%Y-%m-%d")
                if day_str not in grouped_entries:
                    grouped_entries[day_str] = []
                grouped_entries[day_str].append(entry)
                
            forecast_list = []
            # Process each day chronologically
            for day_str in sorted(grouped_entries.keys()):
                day_entries = grouped_entries[day_str]
                
                # Compute temp_min and temp_max of all entries that day
                temp_mins = [e["main"]["temp_min"] for e in day_entries if "main" in e and "temp_min" in e["main"]]
                temp_maxs = [e["main"]["temp_max"] for e in day_entries if "main" in e and "temp_max" in e["main"]]
                
                temp_min_k = min(temp_mins) if temp_mins else None
                temp_max_k = max(temp_maxs) if temp_maxs else None
                
                # Take middle entry closest to 12:00 local time
                middle_entry = min(
                    day_entries, 
                    key=lambda x: abs(datetime.fromtimestamp(x["dt"], tz=tz).hour - 12)
                )
                
                # Extract weather condition from the middle entry
                weather_info = middle_entry.get("weather", [])
                condition = ""
                icon_code = ""
                if weather_info:
                    condition = weather_info[0].get("description", "")
                    icon_code = weather_info[0].get("icon", "")
                    
                icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png" if icon_code else ""
                pop = middle_entry.get("pop", 0)
                
                dt_obj = datetime.strptime(day_str, "%Y-%m-%d")
                
                forecast_list.append({
                    "day_name": dt_obj.strftime("%a"),
                    "date": dt_obj.strftime("%b %d"),
                    "temp_min_k": int(round(temp_min_k)) if temp_min_k is not None else None,
                    "temp_max_k": int(round(temp_max_k)) if temp_max_k is not None else None,
                    "condition": condition.capitalize() if condition else "",
                    "icon_url": icon_url,
                    "pop": pop
                })
                
            # Limit to exactly 5 days (or less if API has fewer)
            result_payload = {
                "forecast": forecast_list[:5]
            }
            
            # Cache the successful response
            cache[forecast_cache_key] = {
                "data": result_payload,
                "timestamp": now
            }
            
            logger.info(f"Successful Forecast API call for city: '{city_normalized}'")
            return jsonify(result_payload)
            
    except Exception as e:
        # 3. Stale forecast fallback
        if forecast_cache_key in cache:
            cache_entry = cache[forecast_cache_key]
            stale_minutes = int(round((now - cache_entry["timestamp"]) / 60.0))
            
            stale_payload = dict(cache_entry["data"])
            stale_payload["stale"] = True
            stale_payload["stale_minutes"] = stale_minutes
            
            logger.warning(f"Forecast API failed, serving stale cache data for: '{city_normalized}' (stale by {stale_minutes} minutes)")
            return jsonify(stale_payload)
            
        # If cache doesn't exist, handle the error gracefully
        logger.error(f"Forecast API failed and no cache exists for: '{city_normalized}'. Error: {e}")
        
        # Map OWM exceptions to frontend friendly responses
        if isinstance(e, ValueError) and "not found" in str(e):
            return jsonify({"error": f"City '{city}' not found."}), 404
            
        if isinstance(e, httpx.HTTPStatusError):
            status_code = e.response.status_code
            if status_code == 401:
                return jsonify({"error": "Service Unavailable: Check OWM API key."}), 503
            elif status_code == 404:
                return jsonify({"error": "City weather data not found."}), 404
                
        # If it was a timeout
        if isinstance(e, httpx.TimeoutException):
            return jsonify({"error": "Gateway Timeout: OpenWeatherMap API did not respond in time."}), 504
            
        return jsonify({"error": "Service Unavailable: Check your internet connection."}), 503

# ==========================================================================
# Phase 5 - Favorites Endpoints
# ==========================================================================
@app.route("/favorites", methods=["GET"])
def get_favorites_list():
    try:
        favs = db.get_favorites()
        return jsonify(favs)
    except Exception as e:
        logger.error(f"Failed to fetch favorites from database: {e}")
        return jsonify({"error": "Failed to load favorites."}), 500

@app.route("/favorites", methods=["POST"])
def add_favorite_city():
    body = request.get_json() or {}
    city = body.get("city", "").strip()
    
    if not city or not sanitize_city(city):
        return jsonify({"error": "Invalid city name format."}), 400
        
    try:
        success, message = db.add_favorite(city)
        if not success:
            return jsonify({"error": message}), 400
        return jsonify({"status": "ok", "message": message}), 201
    except Exception as e:
        logger.error(f"Failed to save favorite: {e}")
        return jsonify({"error": "Internal database error."}), 500

@app.route("/favorites/<city>", methods=["DELETE"])
def remove_favorite_city(city):
    city_clean = city.strip()
    if not city_clean or not sanitize_city(city_clean):
        return jsonify({"error": "Invalid city name format."}), 400
        
    try:
        removed = db.remove_favorite(city_clean)
        if not removed:
            return jsonify({"error": "City not found in favorites."}), 404
        return jsonify({"status": "ok", "message": "Removed from favorites."}), 200
    except Exception as e:
        logger.error(f"Failed to delete favorite: {e}")
        return jsonify({"error": "Internal database error."}), 500

# ==========================================================================
# Production Health Endpoint
# ==========================================================================
@app.route("/health")
def health_check():
    return jsonify({
        "status": "ok",
        "api_key_configured": bool(API_KEY)
    }), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)


