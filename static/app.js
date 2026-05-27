document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const searchForm = document.getElementById("searchForm");
    const cityInput = document.getElementById("cityInput");
    const searchBtn = document.getElementById("searchBtn");
    const btnText = searchBtn.querySelector(".btn-text");
    const loadingOverlay = document.getElementById("loadingOverlay");
    
    const weatherDashboard = document.getElementById("weatherDashboard");
    const errorAlert = document.getElementById("errorAlert");
    const errorMessage = document.getElementById("errorMessage");
    const closeAlertBtn = document.getElementById("closeAlertBtn");
    const staleBanner = document.getElementById("staleBanner");
    const staleBannerText = document.getElementById("staleBannerText");
    
    const locationName = document.getElementById("locationName");
    const locationCountry = document.getElementById("locationCountry");
    const weatherIcon = document.getElementById("weatherIcon");
    const mainTemp = document.getElementById("mainTemp");
    const weatherDesc = document.getElementById("weatherDesc");
    
    const feelsLikeTemp = document.getElementById("feelsLikeTemp");
    const windSpeed = document.getElementById("windSpeed");
    const humidity = document.getElementById("humidity");
    const pressure = document.getElementById("pressure");
    
    const forecastSection = document.getElementById("forecastSection");
    const forecastContainer = document.getElementById("forecastContainer");
    
    const favoritesContainer = document.getElementById("favoritesContainer");
    const favoritesList = document.getElementById("favoritesList");
    const favToggleBtn = document.getElementById("favToggleBtn");
    
    const unitToggle = document.getElementById("unitToggle");
    
    // State variables
    let currentUnit = "C"; // Default unit: Celsius
    let currentData = {
        city: "",
        temp_k: null,
        feels_like_k: null,
        forecast: []
    };
    
    let favorites = [];
    let refreshIntervalId = null;

    // XSS-safe HTML escaper — used wherever dynamic data goes into innerHTML
    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    // Temperature Conversion Helper
    function formatTemperature(kelvin, unit) {
        if (kelvin === null || kelvin === undefined || isNaN(kelvin)) {
            return "--";
        }
        if (unit === "C") {
            return Math.round(kelvin - 273.15);
        } else {
            return Math.round((kelvin - 273.15) * 1.8 + 32);
        }
    }

    // Dynamic Forecast Card Renderer
    function renderForecastCards() {
        forecastContainer.innerHTML = "";
        
        if (!currentData.forecast || currentData.forecast.length === 0) {
            forecastSection.classList.add("hidden");
            return;
        }
        
        currentData.forecast.forEach(day => {
            const minTempStr = formatTemperature(day.temp_min_k, currentUnit);
            const maxTempStr = formatTemperature(day.temp_max_k, currentUnit);
            
            const card = document.createElement("div");
            card.className = "forecast-day-card";
            
            // Format probability of precipitation if > 0
            const popPercent = Math.round(day.pop * 100);
            const popBadgeHtml = popPercent > 0 
                ? `<div class="fc-pop" title="Precipitation Probability">
                     <i data-lucide="droplets"></i>
                     <span>${popPercent}%</span>
                   </div>`
                : "";
                
            // Use escapeHtml on all API-sourced strings to prevent XSS
            card.innerHTML = `
                <div class="fc-day-name">${escapeHtml(day.day_name)}</div>
                <div class="fc-date">${escapeHtml(day.date)}</div>
                <img class="fc-icon" src="${escapeHtml(day.icon_url)}" alt="${escapeHtml(day.condition)}">
                <div class="fc-temp-range">
                    <span class="fc-temp-max">${escapeHtml(maxTempStr)}°</span>
                    <span class="fc-temp-min">${escapeHtml(minTempStr)}°</span>
                </div>
                <div class="fc-condition">${escapeHtml(day.condition)}</div>
                ${popBadgeHtml}
            `;
            
            forecastContainer.appendChild(card);
        });
        
        forecastSection.classList.remove("hidden");
        // Re-trigger Lucide icons in generated cards
        lucide.createIcons();
    }

    // Update UI temperatures based on current data and active unit
    function updateDisplayUnits() {
        mainTemp.textContent = formatTemperature(currentData.temp_k, currentUnit);
        feelsLikeTemp.textContent = formatTemperature(currentData.feels_like_k, currentUnit);
        renderForecastCards();
    }

    // Toggle unit switch handler
    unitToggle.addEventListener("click", () => {
        // Toggle unit
        if (currentUnit === "C") {
            currentUnit = "F";
            unitToggle.classList.add("active");
            unitToggle.setAttribute("data-unit", "F");
        } else {
            currentUnit = "C";
            unitToggle.classList.remove("active");
            unitToggle.setAttribute("data-unit", "C");
        }
        
        // Update display values
        updateDisplayUnits();
    });

    // Alert close button
    closeAlertBtn.addEventListener("click", () => {
        errorAlert.classList.add("hidden");
    });

    // Show Error Utility
    function showError(message) {
        errorMessage.textContent = message;
        errorAlert.classList.remove("hidden");
        errorAlert.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    // Load & Render Favorites
    async function loadFavorites() {
        try {
            const res = await fetch("/favorites");
            if (res.ok) {
                favorites = await res.json();
                renderFavoritesList();
            }
        } catch (err) {
            console.error("Failed to load favorites list:", err);
        }
    }

    function renderFavoritesList() {
        favoritesList.innerHTML = "";
        
        if (favorites.length === 0) {
            favoritesContainer.classList.add("hidden");
            return;
        }
        
        favorites.forEach(city => {
            const btn = document.createElement("button");
            btn.className = "fav-city-btn";
            btn.textContent = city;
            btn.type = "button";
            
            // Search city on click
            btn.addEventListener("click", () => {
                cityInput.value = city;
                triggerSearch(city);
            });
            
            favoritesList.appendChild(btn);
        });
        
        favoritesContainer.classList.remove("hidden");
        syncFavoriteStar();
    }

    // Sync favorite star icon highlight
    function syncFavoriteStar() {
        if (!currentData.city) return;
        const isFav = favorites.some(c => c.toLowerCase() === currentData.city.toLowerCase());
        if (isFav) {
            favToggleBtn.classList.add("pinned");
            favToggleBtn.setAttribute("aria-label", "Remove city from favorites");
        } else {
            favToggleBtn.classList.remove("pinned");
            favToggleBtn.setAttribute("aria-label", "Add city to favorites");
        }
    }

    // Toggle favorite action
    favToggleBtn.addEventListener("click", async () => {
        if (!currentData.city) return;
        
        const isFav = favorites.some(c => c.toLowerCase() === currentData.city.toLowerCase());
        
        try {
            if (isFav) {
                // Remove from favorites
                const res = await fetch(`/favorites/${encodeURIComponent(currentData.city)}`, {
                    method: "DELETE"
                });
                
                if (res.ok) {
                    favorites = favorites.filter(c => c.toLowerCase() !== currentData.city.toLowerCase());
                    renderFavoritesList();
                } else {
                    const errData = await res.json();
                    showError(errData.error || "Failed to remove city from favorites.");
                }
            } else {
                // Add to favorites
                const res = await fetch("/favorites", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ city: currentData.city })
                });
                
                if (res.ok) {
                    favorites.push(currentData.city);
                    renderFavoritesList();
                } else {
                    const errData = await res.json();
                    showError(errData.error || "Failed to add city to favorites.");
                }
            }
        } catch (err) {
            console.error(err);
            showError("Database connection failed.");
        }
    });

    // High Level Fetch & Render Wrapper
    async function fetchWeatherData(city, isAutoRefresh = false) {
        if (!isAutoRefresh) {
            // Hide previous errors & banners
            errorAlert.classList.add("hidden");
            staleBanner.classList.add("hidden");
            
            // Disable button, show loading
            searchBtn.disabled = true;
            btnText.textContent = "Loading...";
            loadingOverlay.classList.remove("hidden");
        }
        
        try {
            // 1. Fetch Current Weather
            const weatherResponse = await fetch(`/weather?city=${encodeURIComponent(city)}`);
            const weatherData = await weatherResponse.json();
            
            if (!weatherResponse.ok) {
                let errorMsg = weatherData.error || "An unexpected error occurred fetching current weather.";
                if (weatherResponse.status === 400) {
                    errorMsg = weatherData.error || "Invalid city name format. Avoid special characters.";
                } else if (weatherResponse.status === 404) {
                    errorMsg = weatherData.error || `City "${city}" not found. Please check spelling.`;
                } else if (weatherResponse.status === 429) {
                    errorMsg = "Too many requests – API rate limit reached. Please wait a moment and try again.";
                } else if (weatherResponse.status === 503) {
                    errorMsg = weatherData.error || "Weather service is currently unavailable.";
                } else if (weatherResponse.status === 504) {
                    errorMsg = weatherData.error || "Request timed out. Please check your connection.";
                }
                
                if (!isAutoRefresh) {
                    showError(errorMsg);
                    weatherDashboard.classList.add("hidden");
                }
                return false;
            }
            
            // 2. Fetch Forecast Weather
            const forecastResponse = await fetch(`/forecast?city=${encodeURIComponent(city)}`);
            const forecastData = await forecastResponse.json();
            
            if (!forecastResponse.ok) {
                if (!isAutoRefresh) {
                    showError(forecastData.error || "An unexpected error occurred fetching the forecast.");
                    weatherDashboard.classList.add("hidden");
                }
                return false;
            }
            
            // Save state
            currentData.city = weatherData.city;
            currentData.temp_k = weatherData.temp_k;
            currentData.feels_like_k = weatherData.feels_like_k;
            currentData.forecast = forecastData.forecast || [];
            
            // Render Current Weather UI Elements
            locationName.textContent = weatherData.city;
            locationCountry.textContent = weatherData.country;
            weatherIcon.src = weatherData.icon_url || "";
            weatherIcon.alt = weatherData.condition || "Weather Icon";
            weatherDesc.textContent = weatherData.condition || "Unknown";
            
            // Round wind speed to 1 decimal place for clean display
            windSpeed.textContent = weatherData.wind_speed !== null ? parseFloat(weatherData.wind_speed).toFixed(1) : "--";
            humidity.textContent = weatherData.humidity !== null ? weatherData.humidity : "--";
            pressure.textContent = weatherData.pressure !== null ? weatherData.pressure : "--";
            
            // Convert and render temperatures (current + forecast)
            updateDisplayUnits();
            syncFavoriteStar();
            
            // Resilience Stale Data Banner handling (Show if EITHER current or forecast is stale)
            const isStale = weatherData.stale || forecastData.stale;
            const staleMins = Math.max(weatherData.stale_minutes || 0, forecastData.stale_minutes || 0);
            
            if (isStale) {
                staleBannerText.textContent = `Showing data from ${staleMins} minutes ago – service unreachable`;
                staleBanner.classList.remove("hidden");
            } else {
                staleBanner.classList.add("hidden");
            }
            
            // Show main dashboard
            weatherDashboard.classList.remove("hidden");
            return true;
            
        } catch (err) {
            console.error(err);
            if (!isAutoRefresh) {
                showError("Could not connect to the server. Please check your internet connection.");
                weatherDashboard.classList.add("hidden");
            }
            return false;
        } finally {
            if (!isAutoRefresh) {
                searchBtn.disabled = false;
                btnText.textContent = "Search";
                loadingOverlay.classList.add("hidden");
            }
        }
    }

    // Trigger Search Helper
    async function triggerSearch(city) {
        // Clear any existing background refresh timers
        if (refreshIntervalId) {
            clearInterval(refreshIntervalId);
            refreshIntervalId = null;
        }
        
        const success = await fetchWeatherData(city, false);
        
        if (success) {
            // Start a new 10-minute auto-refresh interval for this city
            refreshIntervalId = setInterval(() => {
                console.log(`Auto-refreshing weather data for: ${city}`);
                fetchWeatherData(city, true);
            }, 10 * 60 * 1000); // 10 minutes
        }
    }

    // Form Submission Handler
    searchForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const city = cityInput.value.trim();
        if (!city) return;
        triggerSearch(city);
    });

    // Initialize Page
    loadFavorites();
});

