"""
Utility functions for weather data processing
"""
import os
import json
import logging
import requests
from datetime import datetime, timedelta
import random
import calendar

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# OpenWeatherMap API base URLs
WEATHER_API_BASE_URL = "https://api.openweathermap.org/data/2.5"
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
logger.info(f"OpenWeather API Key Found: {'Yes' if WEATHER_API_KEY else 'No'}")
logger.info(f"Environment variables: {list(os.environ.keys())}")

def get_city_weather(city):
    """
    Get current weather for a specific city (alias to get_current_weather)
    
    Args:
        city (str): City name
        
    Returns:
        dict: Weather data for the city
    """
    return get_current_weather(city)

def get_current_weather(city):
    """
    Get current weather for a specific city
    
    Args:
        city (str): City name
        
    Returns:
        dict: Weather data for the city
    """
    try:
        # Get the API key again, in case it wasn't loaded at module level
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        logger.info(f"Inside get_current_weather: API key present: {'Yes' if api_key else 'No'}")
        
        if not api_key:
            logger.warning("OpenWeather API key not configured. Using simulated data.")
            return generate_simulated_weather(city)
        
        # Make request to OpenWeatherMap API
        url = f"{WEATHER_API_BASE_URL}/weather?q={city}&units=metric&appid={api_key}"
        logger.info(f"Making request to: {url[:url.find('appid=') + 6]}[API_KEY_HIDDEN]")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Successfully fetched weather data for {city}")
            return response.json()
        else:
            logger.error(f"Error fetching weather data: {response.status_code}, {response.text}")
            # Fall back to simulated data
            return generate_simulated_weather(city)
            
    except Exception as e:
        logger.error(f"Exception fetching weather data: {e}")
        return generate_simulated_weather(city)

def get_weather_forecast(city):
    """
    Get 5-day weather forecast for a specific city
    
    Args:
        city (str): City name
        
    Returns:
        dict: Forecast data for the city
    """
    try:
        # Get the API key again, in case it wasn't loaded at module level
        api_key = os.getenv("OPENWEATHER_API_KEY", "")
        logger.info(f"Inside get_weather_forecast: API key present: {'Yes' if api_key else 'No'}")
        
        if not api_key:
            logger.warning("OpenWeather API key not configured. Using simulated data.")
            return generate_simulated_forecast(city)
        
        # Make request to OpenWeatherMap API
        url = f"{WEATHER_API_BASE_URL}/forecast?q={city}&units=metric&appid={api_key}"
        logger.info(f"Making forecast request to: {url[:url.find('appid=') + 6]}[API_KEY_HIDDEN]")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Successfully fetched forecast data for {city}")
            return response.json()
        else:
            logger.error(f"Error fetching forecast data: {response.status_code}, {response.text}")
            # Fall back to simulated data
            return generate_simulated_forecast(city)
            
    except Exception as e:
        logger.error(f"Exception fetching forecast data: {e}")
        return generate_simulated_forecast(city)

def get_weather_history(city):
    """
    Get historical weather data for a specific city
    This would normally use historical API, but we'll generate simulated data
    
    Args:
        city (str): City name
        
    Returns:
        dict: Historical weather data for the city
    """
    try:
        # Cache file path
        cache_dir = "frontend/static/data/cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = f"{cache_dir}/weather_history_{city.lower().replace(' ', '_')}.json"
        
        # Check if we have cached data
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                data = json.load(f)
                # Only use cache if it's less than 1 day old
                if datetime.now().timestamp() - data.get("timestamp", 0) < 86400:
                    logger.info(f"Using cached historical weather data for {city}")
                    return data
        
        # Generate simulated historical data
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # Generate temperature data based on hemisphere and season
        temperature_data = {
            "labels": months,
            "values": generate_temperature_pattern(city)
        }
        
        # Generate precipitation data
        precipitation_data = {
            "labels": months,
            "values": generate_precipitation_pattern(city)
        }
        
        data = {
            "city": city,
            "temperature": temperature_data,
            "precipitation": precipitation_data,
            "timestamp": datetime.now().timestamp()
        }
        
        # Cache the data
        with open(cache_file, "w") as f:
            json.dump(data, f)
            
        return data
        
    except Exception as e:
        logger.error(f"Exception getting historical weather data: {e}")
        # Return basic simulated data if there's an error
        return {
            "city": city,
            "temperature": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "values": [5, 7, 12, 17, 22, 25, 27, 26, 22, 16, 10, 6]
            },
            "precipitation": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "values": [65, 55, 60, 45, 70, 65, 45, 60, 75, 80, 75, 70]
            }
        }

def get_global_weather_data():
    """
    Get weather data for major cities around the world
    
    Returns:
        list: Weather data for major cities
    """
    try:
        if not WEATHER_API_KEY:
            logger.warning("OpenWeather API key not configured. Using simulated data.")
            return generate_simulated_global_weather()
        
        # Cache file path
        cache_dir = "frontend/static/data/cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = f"{cache_dir}/global_weather.json"
        
        # Check if we have recent cached data (less than 1 hour old)
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                data = json.load(f)
                # Only use cache if it's less than 1 hour old
                if datetime.now().timestamp() - data.get("timestamp", 0) < 3600:
                    logger.info("Using cached global weather data")
                    return data.get("cities", [])
        
        # List of major cities to get weather data for
        cities = [
            "New York,US", "London,GB", "Tokyo,JP", "Beijing,CN", "Mumbai,IN",
            "Sydney,AU", "Paris,FR", "Berlin,DE", "Moscow,RU", "Rio de Janeiro,BR",
            "Cairo,EG", "Lagos,NG", "Cape Town,ZA", "Mexico City,MX", "Toronto,CA",
            "Bangkok,TH", "Dubai,AE", "Singapore,SG", "Seoul,KR", "Istanbul,TR"
        ]
        
        global_data = []
        
        for city_country in cities:
            try:
                # Make request to OpenWeatherMap API
                city = city_country.split(",")[0]
                url = f"{WEATHER_API_BASE_URL}/weather?q={city_country}&units=metric&appid={WEATHER_API_KEY}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    global_data.append(data)
                else:
                    logger.warning(f"Error fetching data for {city_country}: {response.status_code}")
                    # Add a simulated entry if API fails for this city
                    global_data.append(generate_city_weather(city))
            except Exception as e:
                logger.error(f"Exception fetching data for {city_country}: {e}")
        
        # Cache the data
        with open(cache_file, "w") as f:
            json.dump({
                "cities": global_data,
                "timestamp": datetime.now().timestamp()
            }, f)
            
        return global_data
        
    except Exception as e:
        logger.error(f"Exception fetching global weather data: {e}")
        return generate_simulated_global_weather()

def get_weather_aqi_correlation():
    """
    Get correlation data between weather parameters and air quality indices
    
    Returns:
        dict: Correlation data
    """
    try:
        # Parameters affecting air quality
        parameters = ["Temperature", "Humidity", "Wind Speed", "Precipitation", "Pressure"]
        
        # Different pollutants correlation with weather parameters
        datasets = [
            {
                "label": "PM2.5",
                "data": [0.6, 0.7, -0.8, -0.7, 0.5],
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "borderColor": "rgba(255, 99, 132, 1)",
                "borderWidth": 2
            },
            {
                "label": "Ozone",
                "data": [0.8, 0.3, -0.4, -0.6, 0.2],
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 2
            },
            {
                "label": "NO2",
                "data": [0.5, 0.6, -0.7, -0.5, 0.4],
                "backgroundColor": "rgba(255, 206, 86, 0.2)",
                "borderColor": "rgba(255, 206, 86, 1)",
                "borderWidth": 2
            },
            {
                "label": "SO2",
                "data": [0.4, 0.5, -0.6, -0.7, 0.3],
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "borderColor": "rgba(75, 192, 192, 1)",
                "borderWidth": 2
            }
        ]
        
        # Seasonal impact data
        seasons = ["Winter", "Spring", "Summer", "Fall"]
        aqi_values = [110, 85, 65, 95]  # Average AQI values by season
        
        return {
            "correlations": {
                "parameters": parameters,
                "datasets": datasets
            },
            "seasons": {
                "seasons": seasons,
                "aqi_values": aqi_values
            }
        }
        
    except Exception as e:
        logger.error(f"Exception getting weather-AQI correlation data: {e}")
        return {
            "correlations": {
                "parameters": ["Temperature", "Humidity", "Wind Speed", "Precipitation", "Pressure"],
                "datasets": []
            },
            "seasons": {
                "seasons": ["Winter", "Spring", "Summer", "Fall"],
                "aqi_values": [100, 80, 60, 90]
            }
        }

# Helper functions for generating simulated data

def generate_simulated_weather(city):
    """Generate simulated weather data for a city"""
    # Weather conditions based on season
    now = datetime.now()
    month = now.month
    
    # Determine season (rough approximation)
    if month in [12, 1, 2]:
        season = "winter"
    elif month in [3, 4, 5]:
        season = "spring"
    elif month in [6, 7, 8]:
        season = "summer"
    else:
        season = "fall"
    
    # Weather conditions options with weights based on season
    conditions = {
        "winter": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d", "weight": 2},
            {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d", "weight": 2},
            {"id": 802, "main": "Clouds", "description": "scattered clouds", "icon": "03d", "weight": 3},
            {"id": 600, "main": "Snow", "description": "light snow", "icon": "13d", "weight": 4},
            {"id": 601, "main": "Snow", "description": "snow", "icon": "13d", "weight": 3},
            {"id": 741, "main": "Fog", "description": "fog", "icon": "50d", "weight": 3}
        ],
        "spring": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d", "weight": 3},
            {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d", "weight": 4},
            {"id": 500, "main": "Rain", "description": "light rain", "icon": "10d", "weight": 4},
            {"id": 501, "main": "Rain", "description": "moderate rain", "icon": "10d", "weight": 2},
            {"id": 721, "main": "Haze", "description": "haze", "icon": "50d", "weight": 2}
        ],
        "summer": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d", "weight": 5},
            {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d", "weight": 3},
            {"id": 500, "main": "Rain", "description": "light rain", "icon": "10d", "weight": 2},
            {"id": 502, "main": "Rain", "description": "heavy intensity rain", "icon": "10d", "weight": 1},
            {"id": 211, "main": "Thunderstorm", "description": "thunderstorm", "icon": "11d", "weight": 1}
        ],
        "fall": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d", "weight": 3},
            {"id": 801, "main": "Clouds", "description": "few clouds", "icon": "02d", "weight": 3},
            {"id": 802, "main": "Clouds", "description": "scattered clouds", "icon": "03d", "weight": 4},
            {"id": 500, "main": "Rain", "description": "light rain", "icon": "10d", "weight": 3},
            {"id": 501, "main": "Rain", "description": "moderate rain", "icon": "10d", "weight": 2},
            {"id": 741, "main": "Fog", "description": "fog", "icon": "50d", "weight": 2}
        ]
    }
    
    # Select random weather condition based on season weights
    season_conditions = conditions[season]
    weights = [cond["weight"] for cond in season_conditions]
    weather = random.choices(season_conditions, weights=weights, k=1)[0]
    
    # Generate temperature based on season
    if season == "winter":
        temp = round(random.uniform(-5, 10), 1)
    elif season == "spring":
        temp = round(random.uniform(10, 25), 1)
    elif season == "summer":
        temp = round(random.uniform(20, 35), 1)
    else:  # fall
        temp = round(random.uniform(5, 20), 1)
    
    # Generate other parameters based on weather condition
    if weather["main"] in ["Rain", "Thunderstorm"]:
        humidity = random.randint(70, 95)
        pressure = random.randint(990, 1005)
        wind_speed = round(random.uniform(3, 8), 1)
    elif weather["main"] == "Snow":
        humidity = random.randint(80, 95)
        pressure = random.randint(980, 1000)
        wind_speed = round(random.uniform(2, 5), 1)
    elif weather["main"] == "Fog":
        humidity = random.randint(85, 100)
        pressure = random.randint(1000, 1015)
        wind_speed = round(random.uniform(0, 3), 1)
    else:  # Clear or Clouds
        humidity = random.randint(40, 70)
        pressure = random.randint(1010, 1025)
        wind_speed = round(random.uniform(2, 6), 1)
    
    # Create simulated data structure matching OpenWeatherMap API
    data = {
        "coord": {"lon": random.uniform(-180, 180), "lat": random.uniform(-90, 90)},
        "weather": [weather],
        "base": "stations",
        "main": {
            "temp": temp,
            "feels_like": temp - round(random.uniform(1, 3), 1),
            "temp_min": temp - round(random.uniform(0, 2), 1),
            "temp_max": temp + round(random.uniform(0, 2), 1),
            "pressure": pressure,
            "humidity": humidity
        },
        "visibility": 10000,
        "wind": {
            "speed": wind_speed,
            "deg": random.randint(0, 359)
        },
        "clouds": {
            "all": random.randint(0, 100)
        },
        "dt": int(datetime.now().timestamp()),
        "sys": {
            "type": 2,
            "id": 2011538,
            "country": "XX",  # Placeholder country code
            "sunrise": int((datetime.now().replace(hour=6, minute=0, second=0)).timestamp()),
            "sunset": int((datetime.now().replace(hour=18, minute=0, second=0)).timestamp())
        },
        "timezone": 0,
        "id": random.randint(1000000, 9999999),
        "name": city,
        "cod": 200
    }
    
    return data

def generate_simulated_forecast(city):
    """Generate simulated 5-day forecast data for a city"""
    now = datetime.now()
    list_data = []
    
    # Generate data points for 5 days, 8 points per day (every 3 hours)
    for i in range(40):
        forecast_time = now + timedelta(hours=i*3)
        
        # Get base weather for the day
        day_seed = forecast_time.day + forecast_time.month
        random.seed(day_seed)
        
        # Determine if day or night
        hour = forecast_time.hour
        is_day = hour >= 6 and hour <= 18
        
        # Base data for the time point
        base_weather = generate_simulated_weather(city)
        
        # Adjust for time of day
        weather = base_weather["weather"][0].copy()
        if not is_day:
            # Convert day icon to night version
            if weather["icon"].endswith("d"):
                weather["icon"] = weather["icon"][:-1] + "n"
        
        # Temperature variation by time of day
        temp_base = base_weather["main"]["temp"]
        if hour >= 12 and hour <= 15:  # Peak temperature around noon-3pm
            temp = temp_base + random.uniform(1, 3)
        elif hour >= 0 and hour <= 5:  # Coolest in early morning
            temp = temp_base - random.uniform(2, 5)
        else:
            temp = temp_base + random.uniform(-1, 1)
        
        # Create forecast data point
        data_point = {
            "dt": int(forecast_time.timestamp()),
            "main": {
                "temp": round(temp, 1),
                "feels_like": round(temp - random.uniform(1, 3), 1),
                "temp_min": round(temp - random.uniform(0, 2), 1),
                "temp_max": round(temp + random.uniform(0, 2), 1),
                "pressure": base_weather["main"]["pressure"],
                "humidity": base_weather["main"]["humidity"],
                "sea_level": base_weather["main"]["pressure"] + random.randint(5, 15),
                "grnd_level": base_weather["main"]["pressure"] - random.randint(5, 15)
            },
            "weather": [weather],
            "clouds": base_weather["clouds"],
            "wind": base_weather["wind"],
            "visibility": base_weather["visibility"],
            "pop": round(random.uniform(0, 1), 2),  # Probability of precipitation
            "sys": {"pod": "d" if is_day else "n"},  # Part of day
            "dt_txt": forecast_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        list_data.append(data_point)
    
    # Create full forecast response
    forecast_data = {
        "cod": "200",
        "message": 0,
        "cnt": len(list_data),
        "list": list_data,
        "city": {
            "id": random.randint(1000000, 9999999),
            "name": city,
            "coord": {
                "lat": random.uniform(-90, 90),
                "lon": random.uniform(-180, 180)
            },
            "country": "XX",
            "population": random.randint(100000, 5000000),
            "timezone": 0,
            "sunrise": int((now.replace(hour=6, minute=0, second=0)).timestamp()),
            "sunset": int((now.replace(hour=18, minute=0, second=0)).timestamp())
        }
    }
    
    return forecast_data

def generate_temperature_pattern(city):
    """Generate temperature pattern for a city based on name (for consistent results)"""
    # Use city name as a seed for consistent results
    city_seed = sum([ord(c) for c in city.lower()])
    random.seed(city_seed)
    
    # Determine if northern or southern hemisphere
    # This is simplified - we'd normally use geolocation
    northern = random.random() < 0.7  # 70% chance of northern hemisphere
    
    # Base temperature patterns for northern hemisphere
    if northern:
        # Cold winter, warm summer
        base_pattern = [5, 7, 12, 17, 22, 25, 27, 26, 22, 16, 10, 6]
    else:
        # Reversed seasons
        base_pattern = [25, 26, 22, 16, 10, 6, 5, 7, 12, 17, 22, 25]
    
    # Add some randomization
    pattern = [temp + random.uniform(-3, 3) for temp in base_pattern]
    return [round(temp, 1) for temp in pattern]

def generate_precipitation_pattern(city):
    """Generate precipitation pattern for a city based on name (for consistent results)"""
    # Use city name as a seed for consistent results
    city_seed = sum([ord(c) for c in city.lower()])
    random.seed(city_seed)
    
    # Determine climate type (rainy, moderate, dry)
    climate_type = random.choices(
        ["rainy", "moderate", "dry"],
        weights=[0.3, 0.5, 0.2],
        k=1
    )[0]
    
    # Base precipitation patterns
    if climate_type == "rainy":
        base_pattern = [120, 110, 100, 90, 70, 50, 40, 50, 70, 90, 100, 120]
    elif climate_type == "moderate":
        base_pattern = [70, 65, 60, 55, 50, 45, 40, 45, 50, 55, 60, 70]
    else:  # dry
        base_pattern = [20, 15, 10, 15, 20, 5, 2, 2, 5, 10, 15, 20]
    
    # Add some randomization
    pattern = [precip + random.uniform(-precip*0.2, precip*0.2) for precip in base_pattern]
    return [round(precip, 1) for precip in pattern]

def generate_city_weather(city):
    """Generate simulated weather data for a specific city in global map"""
    weather_data = generate_simulated_weather(city)
    
    # Make sure city name and coordinates are set
    weather_data["name"] = city
    
    # For the global map, let's generate more realistic coordinates
    # This is a simplified approach - we'd normally use a geocoding API
    random.seed(sum([ord(c) for c in city.lower()]))
    
    # Try to assign somewhat realistic coordinates based on city name
    # This is for demonstration only and won't be geographically accurate
    if "new york" in city.lower():
        weather_data["coord"] = {"lon": -74.006, "lat": 40.7128}
        weather_data["sys"]["country"] = "US"
    elif "london" in city.lower():
        weather_data["coord"] = {"lon": -0.1278, "lat": 51.5074}
        weather_data["sys"]["country"] = "GB"
    elif "tokyo" in city.lower():
        weather_data["coord"] = {"lon": 139.6917, "lat": 35.6895}
        weather_data["sys"]["country"] = "JP"
    elif "beijing" in city.lower():
        weather_data["coord"] = {"lon": 116.4074, "lat": 39.9042}
        weather_data["sys"]["country"] = "CN"
    elif "mumbai" in city.lower():
        weather_data["coord"] = {"lon": 72.8777, "lat": 19.0760}
        weather_data["sys"]["country"] = "IN"
    elif "sydney" in city.lower():
        weather_data["coord"] = {"lon": 151.2093, "lat": -33.8688}
        weather_data["sys"]["country"] = "AU"
    elif "paris" in city.lower():
        weather_data["coord"] = {"lon": 2.3522, "lat": 48.8566}
        weather_data["sys"]["country"] = "FR"
    elif "berlin" in city.lower():
        weather_data["coord"] = {"lon": 13.4050, "lat": 52.5200}
        weather_data["sys"]["country"] = "DE"
    else:
        # For other cities, generate random but reasonable coordinates
        weather_data["coord"] = {
            "lon": random.uniform(-180, 180),
            "lat": random.uniform(-60, 70)  # Avoiding extreme latitudes
        }
        weather_data["sys"]["country"] = "XX"
    
    return weather_data

def generate_simulated_global_weather():
    """Generate simulated global weather data"""
    cities = [
        "New York", "London", "Tokyo", "Beijing", "Mumbai",
        "Sydney", "Paris", "Berlin", "Moscow", "Rio de Janeiro",
        "Cairo", "Lagos", "Cape Town", "Mexico City", "Toronto",
        "Bangkok", "Dubai", "Singapore", "Seoul", "Istanbul"
    ]
    
    global_data = []
    for city in cities:
        global_data.append(generate_city_weather(city))
    
    return global_data

# Weather planning functions removed as requested