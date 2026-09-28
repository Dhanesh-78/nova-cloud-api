import requests


def get_weather(city: str):

    city = city.strip()

    if not city:
        return {
            "success": False,
            "message": "Please tell me the city name."
        }

    try:

        # ==========================================
        # Find city coordinates
        # ==========================================

        geo_url = "https://geocoding-api.open-meteo.com/v1/search"

        geo_response = requests.get(
            geo_url,
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            },
            timeout=10
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()

        results = geo_data.get("results")

        if not results:
            return {
                "success": False,
                "message": f"I couldn't find the location {city}."
            }

        location = results[0]

        latitude = location["latitude"]
        longitude = location["longitude"]

        location_name = location.get("name", city)
        country = location.get("country", "")

        # ==========================================
        # Get current weather
        # ==========================================

        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_response = requests.get(
            weather_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto"
            },
            timeout=10
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        current = weather_data.get("current", {})

        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        feels_like = current.get("apparent_temperature")
        precipitation = current.get("precipitation")
        wind_speed = current.get("wind_speed_10m")
        weather_code = current.get("weather_code")

        description = weather_description(weather_code)

        return {
            "success": True,
            "city": location_name,
            "country": country,
            "temperature": temperature,
            "humidity": humidity,
            "feels_like": feels_like,
            "precipitation": precipitation,
            "wind_speed": wind_speed,
            "description": description
        }

    except requests.exceptions.RequestException as e:

        print("Weather API error:", e)

        return {
            "success": False,
            "message": "I couldn't reach the weather service."
        }

    except Exception as e:

        print("Weather error:", e)

        return {
            "success": False,
            "message": "Something went wrong while getting the weather."
        }


def weather_description(code):

    descriptions = {
        0: "clear sky",

        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",

        45: "fog",
        48: "depositing rime fog",

        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",

        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",

        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",

        80: "slight rain showers",
        81: "moderate rain showers",
        82: "violent rain showers",

        95: "thunderstorm",
        96: "thunderstorm with slight hail",
        99: "thunderstorm with heavy hail"
    }

    return descriptions.get(
        code,
        "unknown conditions"
    )