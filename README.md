\# ☁️ AeroSky – Smart Weather Dashboard



A production‑ready weather dashboard that shows current conditions and a 5‑day forecast for any city. Built with resilience in mind – caching, retries, offline fallback, and logging.



!\[Python](https://img.shields.io/badge/Python-3.10-blue) !\[Flask](https://img.shields.io/badge/Flask-3.0-green) !\[License](https://img.shields.io/badge/License-MIT-yellow)



\## ✨ Features



\- ✅ \*\*Current weather \& 5‑day forecast\*\* – OpenWeatherMap API

\- ✅ \*\*°C / °F toggle\*\* – client‑side conversion, no refetch

\- ✅ \*\*Favorites\*\* – save up to 5 cities (SQLite)

\- ✅ \*\*Smart caching\*\* – 10‑minute in‑memory cache

\- ✅ \*\*Resilient\*\* – exponential backoff retries, stale‑data fallback with warning banner

\- ✅ \*\*Auto‑refresh\*\* – refreshes every 10 minutes

\- ✅ \*\*Logging\*\* – rotating logs (INFO, WARNING, ERROR)

\- ✅ \*\*Unit tested\*\* – `pytest` for conversions, cache, sanitisation

\- ✅ \*\*Production server\*\* – Waitress WSGI



\## 🛠️ Tech Stack



| Layer       | Technology |

|-------------|------------|

| Backend     | Python 3.10, Flask, httpx |

| Frontend    | HTML5, CSS3, Vanilla JavaScript |

| Database    | SQLite (favourites) |

| Testing     | pytest |

| Server      | Waitress |



\## 🚀 Getting Started



\### Prerequisites

\- Python 3.10+

\- Git

\- \[OpenWeatherMap API key](https://openweathermap.org/api) (free)



\### Installation



1\. \*\*Clone the repository\*\*

&#x20;  ```bash

&#x20;  git clone https://github.com/HaiderAli1076/AeroSky.git

&#x20;  cd AeroSky

