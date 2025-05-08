import os

# Flask app configuration
DEBUG = True
SECRET_KEY = os.environ.get("SESSION_SECRET", "dev_key_for_testing")
PORT = 5000
HOST = '0.0.0.0'

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///air_quality.db")

# Data sources
AQI_IN_URL = "https://www.aqi.in/in/world-air-quality-report"
IQAIR_URL = "https://www.iqair.com/in-en/world-most-polluted-cities"

# API configurations
AQICN_API_KEY = os.environ.get('AQICN_API_KEY', '3dc447e982a5cc571500f0747d43eb0e7f095a62')
IQAIR_API_KEY = "09c34ded30cd4cea81443728250305"
IQAIR_API_URL = "https://api.airvisual.com/v2"
WEATHER_API_KEY = "09c34ded30cd4cea81443728250305"

# Data file paths
MARKER_DATA_PATH = 'static/data/marker_data.json'
COUNTRIES_DATA_PATH = 'static/data/countries_data.json'
CITIES_MONTHLY_DATA_PATH = 'static/data/cities_monthly_data.json'

# AQI categories and corresponding colors
AQI_CATEGORIES = {
    'Good': {'min': 0, 'max': 50, 'color': 'green'},
    'Moderate': {'min': 51, 'max': 100, 'color': 'yellow'},
    'Unhealthy for Sensitive Groups': {'min': 101, 'max': 150, 'color': 'orange'},
    'Unhealthy': {'min': 151, 'max': 200, 'color': 'red'},
    'Very Unhealthy': {'min': 201, 'max': 300, 'color': 'purple'},
    'Hazardous': {'min': 301, 'max': 500, 'color': 'maroon'}
}

# Map settings
DEFAULT_MAP_CENTER = [20.0, 0.0]
DEFAULT_ZOOM_LEVEL = 2
MAP_PROVIDER = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
