"""Weather tool using OpenWeatherMap API."""
import requests
from langchain_core.tools import tool
from app.config import config

_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"


@tool
def get_weather(city: str, days: int = 5) -> dict:
    """Get weather forecast for a city. Returns temperature, rain, and conditions per day."""
    params = {
        "q": city + ",VN",
        "appid": config.OPENWEATHERMAP_API_KEY,
        "units": "metric",
        "lang": "vi",
        "cnt": min(days * 8, 40),
    }

    for attempt in range(2):
        try:
            resp = requests.get(_BASE_URL, params=params, timeout=10)
            if resp.status_code == 404:
                raise ValueError(f"City not found: {city}")
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.exceptions.Timeout:
            if attempt == 1:
                raise RuntimeError(f"Weather API timeout for city: {city}")

    daily: dict[str, dict] = {}
    for item in data["list"]:
        date = item["dt_txt"][:10]
        if date not in daily:
            daily[date] = {
                "date": date,
                "temp_min": item["main"]["temp_min"],
                "temp_max": item["main"]["temp_max"],
                "description": item["weather"][0]["description"],
                "rain_mm": item.get("rain", {}).get("3h", 0),
            }
        else:
            daily[date]["temp_min"] = min(daily[date]["temp_min"], item["main"]["temp_min"])
            daily[date]["temp_max"] = max(daily[date]["temp_max"], item["main"]["temp_max"])
            daily[date]["rain_mm"] += item.get("rain", {}).get("3h", 0)

    forecast = list(daily.values())[:days]
    return {"city": city, "forecast": forecast}
