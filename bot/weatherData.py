import os
from dotenv import load_dotenv
import requests
import time


load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

_cache = {}  # zipcode -> {"data": ..., "fetched": ...}

def getCachedData(zipcode, max_age=900):  # 900 s = 15 minutes
    zipcode = str(zipcode)
    entry = _cache.get(zipcode)

    if entry is None or time.time() - entry["fetched"] > max_age:
        fresh = getDayData(zipcode)
        if fresh is not None:
            _cache[zipcode] = {"data": fresh, "fetched": time.time()}
            return fresh
        # request failed: fall back to the old data if we have any
        return entry["data"] if entry else None

    return entry["data"]

def getDayData(zipcode):
    try:
        res = requests.get(
            "https://api.weatherapi.com/v1/forecast.json",
            params={"key": API_KEY, "q": zipcode, "days": 1},
            timeout=10,
        )
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        print(f"Weather request failed: {e}")
        return None

def daySummary(data):
    if data is None:
        return "Couldn't get the weather today."

    day_data = data["forecast"]["forecastday"][0]
    day = day_data["day"]
    temps = extremeTemps(data)
    rain = rainChance(data)
    snow = snowChance(data)

    lines = [
        f"Weather for {data['location']['name']} today: {day['condition']['text']}",
        f"Feels like {temps['low']:.0f}°F to {temps['high']:.0f}°F",
    ]

    # Only mention precipitation when it's actually likely
    if rain > 0:
        lines.append(f"Rain chance: {rain}%")
    if snow > 0:
        lines.append(f"Snow chance: {snow}%")
    if day["totalprecip_in"] > 0:
        lines.append(f"Expected precipitation: {day['totalprecip_in']} in")

    lines.append(f"Max wind: {day['maxwind_mph']:.0f} mph")
    lines.append(f"Sunrise {day_data['astro']['sunrise']}, sunset {day_data['astro']['sunset']}")

    return "\n".join(lines)


def weatherNow(data):
    if data is None:
        return "Couldn't get the weather right now."

    current = data["current"]

    # chance_of_rain/snow are hourly fields, so grab the entry for the current local hour
    local_hour = int(data["location"]["localtime"].split(" ")[1].split(":")[0])
    hour = data["forecast"]["forecastday"][0]["hour"][local_hour]

    lines = [
        f"Right now in {data['location']['name']}: {current['condition']['text']}",
        f"{current['temp_f']:.0f}°F, feels like {current['feelslike_f']:.0f}°F",
    ]

    if hour["chance_of_rain"] > 0:
        lines.append(f"Rain chance: {hour['chance_of_rain']}%")
    if hour["chance_of_snow"] > 0:
        lines.append(f"Snow chance: {hour['chance_of_snow']}%")

    lines.append(f"Wind: {current['wind_mph']:.0f} mph (gusts {current['gust_mph']:.0f} mph)")

    return "\n".join(lines)


def rainChance(data):
    if(data is None):
            return "couldnt get the weather today"
    today = data["forecast"]["forecastday"][0]["hour"]
    rainchance = 0
    for i in range(7, 23):
        if(today[i]["chance_of_rain"]>rainchance):
            rainchance = today[i]["chance_of_rain"]
    return rainchance
    
def snowChance(data):
    if(data is None):
            return "couldnt get the weather today"
    today = data["forecast"]["forecastday"][0]["hour"]
    snowchance = 0
    for i in range(7, 23):
        if today[i]["chance_of_snow"] > snowchance:
            snowchance = today[i]["chance_of_snow"]
    return snowchance

def extremeTemps(data):
    if(data is None):
            return "couldnt get the weather today"
    today = data["forecast"]["forecastday"][0]["hour"]
    max = -5000000
    min = 5000000
    for i in range(7, 23):
            if today[i]["feelslike_f"] > max:
                max = today[i]["feelslike_f"]
            if today[i]["feelslike_f"] < min:
                min = today[i]["feelslike_f"]
    return {"low":min,"high":max}

