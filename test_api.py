import os
import sys
import httpx
from dotenv import load_dotenv

def main():
    # 1. Load API key from .env file
    load_dotenv()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("check key")
        sys.exit(1)
        
    # 2. Prompt user for city name
    try:
        city = input("Enter city name: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        sys.exit(0)
        
    if not city:
        print("not found")
        sys.exit(1)
        
    # 3. Call the geocoding API
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    
    try:
        response = httpx.get(geo_url)
        
        # Check for unauthorized (invalid key)
        if response.status_code == 401:
            print("check key")
            sys.exit(1)
            
        response.raise_for_status()
        geo_data = response.json()
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("check key")
        else:
            print("check internet")
        sys.exit(1)
    except httpx.RequestError:
        print("check internet")
        sys.exit(1)
        
    # 4. Extract lat and lon from the response
    if not geo_data:
        print("not found")
        sys.exit(1)
        
    location = geo_data[0]
    lat = location.get("lat")
    lon = location.get("lon")
    city_name = location.get("name")
    country = location.get("country")
    
    if lat is None or lon is None:
        print("not found")
        sys.exit(1)
        
    # 5. Call the current weather API
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    
    try:
        response = httpx.get(weather_url)
        if response.status_code == 401:
            print("check key")
            sys.exit(1)
        response.raise_for_status()
        weather_data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print("check key")
        else:
            print("check internet")
        sys.exit(1)
    except httpx.RequestError:
        print("check internet")
        sys.exit(1)
        
    # 6. Print results
    #   - City name, country
    #   - Temperature in Kelvin
    #   - Weather description
    temp_k = weather_data.get("main", {}).get("temp")
    description = ""
    weather_list = weather_data.get("weather", [])
    if weather_list:
        description = weather_list[0].get("description", "")
        
    print(f"City: {city_name}, {country}")
    print(f"Temperature: {temp_k} K")
    print(f"Description: {description}")

if __name__ == "__main__":
    main()
