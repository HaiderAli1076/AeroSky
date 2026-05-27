import os
import sys

# Ensure parent directory is in sys.path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import sanitize_city

def test_valid_city_names():
    assert sanitize_city("London") is True
    assert sanitize_city("New York") is True
    assert sanitize_city("Tokyo-to") is True
    assert sanitize_city("Sao Paulo") is True
    assert sanitize_city("Kiel") is True

def test_invalid_city_names():
    # Special characters forbidden: < > & ; ' " ( )
    assert sanitize_city("London<") is False
    assert sanitize_city("New;York") is False
    assert sanitize_city("Tokyo&") is False
    assert sanitize_city("Sao'Paulo") is False
    assert sanitize_city("Paris()") is False
    assert sanitize_city("Berlin\"") is False
    assert sanitize_city(">Madrid") is False

def test_city_length():
    # Length > 100 should be rejected
    assert sanitize_city("A" * 101) is False
    # Max allowed length is 100
    assert sanitize_city("A" * 100) is True
