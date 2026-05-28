
# ☁️ AeroSky – Smart Weather Dashboard

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://HaiderAli1076.pythonanywhere.com)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![OpenWeatherMap](https://img.shields.io/badge/API-OpenWeatherMap-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

A production‑ready weather dashboard that shows current conditions and a 5‑day forecast for any city. Built with resilience in mind – caching, retries, offline fallback, and logging.

🌐 **Live Demo:** [https://HaiderAli1076.pythonanywhere.com](https://HaiderAli1076.pythonanywhere.com)

## ✨ Features

- ✅ **Current weather & 5‑day forecast** – OpenWeatherMap API
- ✅ **°C / °F toggle** – client‑side conversion, no refetch
- ✅ **Favorites** – save up to 5 cities (SQLite)
- ✅ **Smart caching** – 10‑minute in‑memory cache
- ✅ **Resilient** – exponential backoff retries, stale‑data fallback with warning banner
- ✅ **Auto‑refresh** – refreshes every 10 minutes
- ✅ **Logging** – rotating logs (INFO, WARNING, ERROR)
- ✅ **Unit tested** – `pytest` for conversions, cache, sanitisation
- ✅ **Production server** – Waitress WSGI

## 🛠️ Tech Stack

| Layer       | Technology |
|-------------|------------|
| Backend     | Python 3.10, Flask, httpx |
| Frontend    | HTML5, CSS3, Vanilla JavaScript |
| Database    | SQLite (favourites) |
| Testing     | pytest |
| Server      | Waitress |

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Git
- [OpenWeatherMap API key](https://openweathermap.org/api) (free)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/HaiderAli1076/AeroSky.git
   cd AeroSky