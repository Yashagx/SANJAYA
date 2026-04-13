import requests
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Seasonal risk calendar
MONSOON_REGIONS = ["mumbai","chennai","kolkata","kochi","goa",
                   "mangalore","vizag","india","bay of bengal"]
CYCLONE_REGIONS = ["bay of bengal","arabian sea","myanmar",
                   "bangladesh","odisha","andhra"]
GULF_REGIONS    = ["hormuz","gulf","khor fakkan","dubai",
                   "muscat","abu dhabi","doha","kuwait"]
WINTER_FOG      = ["delhi","lahore","karachi","north india",
                   "punjab","haryana","lucknow","varanasi"]
TYPHOON_REGIONS = ["shanghai","hong kong","taiwan","philippines",
                   "south china sea","tokyo","osaka","manila"]

def get_season(month: int, location: str) -> dict:
    loc = location.lower()
    risks = {"season": "normal", "seasonal_boost": 0.10, "reason": "Normal conditions"}

    # Monsoon (June-Sept) — Indian subcontinent
    if month in [6,7,8,9] and any(r in loc for r in MONSOON_REGIONS):
        risks = {"season":"monsoon","seasonal_boost":0.40,
                 "reason":"Active monsoon — severe flooding and road disruption risk"}

    # Cyclone season (Oct-Dec Bay of Bengal, Apr-Jun Arabian Sea)
    elif (month in [10,11,12] and any(r in loc for r in CYCLONE_REGIONS)):
        risks = {"season":"cyclone","seasonal_boost":0.35,
                 "reason":"Cyclone season — Bay of Bengal high alert"}

    # Winter fog (Dec-Feb North India)
    elif month in [12,1,2] and any(r in loc for r in WINTER_FOG):
        risks = {"season":"winter_fog","seasonal_boost":0.30,
                 "reason":"Dense winter fog — severe visibility disruption"}

    # Peak shipping congestion (Nov-Dec global)
    elif month in [11,12]:
        risks = {"season":"peak_shipping","seasonal_boost":0.15,
                 "reason":"Peak holiday shipping season — port congestion elevated"}

    # Gulf dust storms (March-May)
    elif month in [3,4,5] and any(r in loc for r in GULF_REGIONS):
        risks = {"season":"dust_storm","seasonal_boost":0.20,
                 "reason":"Gulf shamal dust storm season"}

    # Typhoon season (July-Oct Pacific)
    elif month in [7,8,9,10] and any(r in loc for r in TYPHOON_REGIONS):
        risks = {"season":"typhoon","seasonal_boost":0.35,
                 "reason":"Typhoon season — Pacific routes high risk"}

    return risks

def get_region_baseline(location: str) -> float:
    loc = location.lower()
    if any(r in loc for r in GULF_REGIONS):      return 0.30
    if any(r in loc for r in CYCLONE_REGIONS):   return 0.25
    if any(r in loc for r in TYPHOON_REGIONS):   return 0.20
    if any(r in loc for r in MONSOON_REGIONS):   return 0.20
    return 0.10  # global minimum floor — weather NEVER zero

def get_weather_risk(location: str, month: int = None) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if month is None:
        month = datetime.now().month

    baseline   = get_region_baseline(location)
    season_ctx = get_season(month, location)
    floor      = max(baseline, 0.10)  # HARD FLOOR — never zero

    try:
        resp = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": location, "appid": api_key, "units": "metric"},
            timeout=5
        )
        data = resp.json()

        if resp.status_code != 200:
            # Use seasonal floor if API can't find location
            score = min(floor + season_ctx["seasonal_boost"], 0.95)
            return {
                "score": round(score, 3),
                "condition": f"Seasonal estimate ({season_ctx['season']})",
                "wind_speed": 0,
                "seasonal_context": season_ctx,
                "floor_applied": True,
                "location_queried": location
            }

        wind     = data.get("wind",{}).get("speed", 0)
        wid      = data.get("weather",[{}])[0].get("id", 800)
        cond     = data.get("weather",[{}])[0].get("description","clear")
        humidity = data.get("main",{}).get("humidity", 50)

        # Severity from weather code
        if wid < 300:   severity = 0.90  # Thunderstorm
        elif wid < 400: severity = 0.35  # Drizzle
        elif wid < 600: severity = 0.55  # Rain
        elif wid < 700: severity = 0.75  # Snow
        elif wid < 800: severity = 0.65  # Fog/dust/haze
        else:           severity = 0.05  # Clear/cloudy

        wind_score = min(wind / 25.0, 1.0)

        # Humidity amplifier (>85% = tropical moisture)
        humidity_boost = 0.10 if humidity > 85 else 0.0

        live_score = (wind_score * 0.35) + (severity * 0.50) + humidity_boost
        seasonal_score = live_score + season_ctx["seasonal_boost"]
        final_score = max(floor, min(seasonal_score, 0.98))

        return {
            "score": round(final_score, 3),
            "condition": cond,
            "wind_speed": wind,
            "humidity": humidity,
            "weather_severity": severity,
            "seasonal_context": season_ctx,
            "floor_applied": final_score == floor,
            "location_queried": location
        }

    except Exception as e:
        score = min(floor + season_ctx["seasonal_boost"], 0.95)
        return {
            "score": round(score, 3),
            "condition": f"API error — seasonal estimate used",
            "seasonal_context": season_ctx,
            "error": str(e),
            "location_queried": location
        }
