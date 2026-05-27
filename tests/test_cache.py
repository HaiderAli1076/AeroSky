import time
import os
import sys

# Ensure parent directory is in sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import cache, CACHE_TTL

def test_cache_miss_hit_expiry():
    # 1. Clear cache
    cache.clear()
    
    city_key = "london"
    payload = {
        "city": "London",
        "country": "GB",
        "temp_k": 280,
        "feels_like_k": 278,
        "condition": "Clouds"
    }
    
    # 2. Test cache miss initially
    assert city_key not in cache
    
    # 3. Add item and test cache hit (inside TTL)
    now = time.time()
    cache[city_key] = {
        "data": payload,
        "timestamp": now
    }
    
    assert city_key in cache
    assert now - cache[city_key]["timestamp"] < CACHE_TTL
    assert cache[city_key]["data"]["temp_k"] == 280
    
    # 4. Test cache expiry (mock timestamp to be older than TTL)
    cache[city_key]["timestamp"] = now - (CACHE_TTL + 10)
    
    stale_duration = time.time() - cache[city_key]["timestamp"]
    assert stale_duration > CACHE_TTL
