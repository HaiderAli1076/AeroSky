import math

def convert_temp(kelvin, unit="C"):
    """
    Python equivalent of JavaScript Math.round() behavior: math.floor(x + 0.5).
    """
    if kelvin is None:
        return None
    
    celsius = kelvin - 273.15
    if unit == "C":
        return math.floor(celsius + 0.5)
    else:
        fahrenheit = celsius * 1.8 + 32
        return math.floor(fahrenheit + 0.5)

def test_kelvin_to_celsius():
    # 0 Kelvin to Celsius
    assert convert_temp(0, "C") == -273
    # Standard freezing point
    assert convert_temp(273.15, "C") == 0
    # Warm day
    assert convert_temp(300.0, "C") == 27
    # Boundary rounding cases
    assert convert_temp(272.6, "C") == -1  # 272.6 - 273.15 = -0.55 -> -1
    assert convert_temp(273.65, "C") == 1  # 273.65 - 273.15 = 0.5 -> 1

def test_kelvin_to_fahrenheit():
    # Absolute zero to Fahrenheit
    assert convert_temp(0, "F") == -460
    # Standard freezing point
    assert convert_temp(273.15, "F") == 32
    # Warm day: (300 - 273.15) * 1.8 + 32 = 48.33 + 32 = 80.33 -> 80
    assert convert_temp(300.0, "F") == 80
    # Precise boiling point
    assert convert_temp(373.15, "F") == 212
