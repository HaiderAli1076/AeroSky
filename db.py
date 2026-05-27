import sqlite3
import os

DB_PATH = "favorites.db"

def init_db():
    """
    Initializes the favorites database and creates the cities table if it doesn't exist.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        conn.commit()

def get_favorites() -> list[str]:
    """
    Retrieves all favorite city names in alphabetical order.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM cities ORDER BY name ASC")
        return [row[0] for row in cursor.fetchall()]

def add_favorite(city: str) -> tuple[bool, str]:
    """
    Adds a city to favorites, enforcing a hard limit of 5 favorites.
    Returns: (success_bool, message_str)
    """
    city_clean = city.strip()
    if not city_clean:
        return False, "City name cannot be empty."
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Enforce count limit
        cursor.execute("SELECT COUNT(*) FROM cities")
        count = cursor.fetchone()[0]
        if count >= 5:
            return False, "Maximum limit of 5 favorites reached. Delete one to add another."
            
        # 2. Insert city name
        try:
            cursor.execute("INSERT INTO cities (name) VALUES (?)", (city_clean,))
            conn.commit()
            return True, "Added to favorites."
        except sqlite3.IntegrityError:
            # City already exists in favorites database
            return True, "Already in favorites."

def remove_favorite(city: str) -> bool:
    """
    Removes a city from favorites. Case insensitive deletion.
    """
    city_clean = city.strip()
    if not city_clean:
        return False
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cities WHERE LOWER(name) = LOWER(?)", (city_clean.lower(),))
        conn.commit()
        return cursor.rowcount > 0
