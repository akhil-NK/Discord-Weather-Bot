import os
from dotenv import load_dotenv
import requests


load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")

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
    if(data == None):
        return "couldnt get the weather today"
    day_data = data["forecast"]["forecastday"][0]
    day = day_data["day"]
    return {
        "location": data["location"]["name"],
        "condition": day["condition"]["text"],
        "temps": extremeTemps(data),
        "rain_chance": rainChance(data),
        "snow_chance": snowChance(data),
        "total_precip_in": day["totalprecip_in"],
        "max_wind_mph": day["maxwind_mph"],
        "sunrise": day_data["astro"]["sunrise"],
        "sunset": day_data["astro"]["sunset"],
    }

def rainChance(data):
    if(data == None):
            return "couldnt get the weather today"
    today = data["forecast"]["forecastday"][0]["hour"]
    rainchance = 0
    for i in range(7, 23):
        if(today[i]["chance_of_rain"]>rainchance):
            rainchance = today[i]["chance_of_rain"]
    return rainchance
    
def snowChance(data):
    if(data == None):
            return "couldnt get the weather today"
    today = data["forecast"]["forecastday"][0]["hour"]
    snowchance = 0
    for i in range(7, 23):
        if today[i]["chance_of_snow"] > snowchance:
            snowchance = today[i]["chance_of_snow"]
    return snowchance

def extremeTemps(data):
    if(data == None):
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

