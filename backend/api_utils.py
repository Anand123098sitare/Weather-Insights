import os
import logging
import json
import requests
from datetime import datetime
from collections import defaultdict
from backend.config import AQICN_API_KEY, IQAIR_API_KEY, IQAIR_API_URL

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
AQICN_BASE_URL = "https://api.waqi.info"

def get_city_air_quality(city_name):
    """
    Get air quality data for a specific city
    
    Args:
        city_name (str): Name of the city
        
    Returns:
        dict: Air quality data for the city
    """
    try:
        logger.info(f"Fetching air quality data for {city_name} from AQICN API")
        url = f"{AQICN_BASE_URL}/feed/{city_name}/?token={AQICN_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'ok':
            result = {
                "city": city_name,
                "aqi": data['data']['aqi'],
                "category": get_aqi_category(data['data']['aqi']),
                "pollutants": {},
                "coordinates": {
                    "lat": data['data'].get('city', {}).get('geo', [0, 0])[0],
                    "lon": data['data'].get('city', {}).get('geo', [0, 0])[1]
                }
            }
            
            # Extract main pollutant
            main_pollutant = None
            max_pollutant_value = 0
            
            if 'iaqi' in data['data']:
                iaqi = data['data']['iaqi']
                pollutant_map = {
                    'pm25': 'PM2.5',
                    'pm10': 'PM10',
                    'o3': 'Ozone',
                    'no2': 'Nitrogen Dioxide',
                    'so2': 'Sulfur Dioxide',
                    'co': 'Carbon Monoxide'
                }
                
                for key, display_name in pollutant_map.items():
                    if key in iaqi:
                        value = iaqi[key]['v']
                        result['pollutants'][key] = value
                        
                        # Track main pollutant (highest value)
                        if value > max_pollutant_value:
                            max_pollutant_value = value
                            main_pollutant = display_name
            
            result['main_pollutant'] = main_pollutant or "Unknown"
            
            # Add station name and time if available
            if 'city' in data['data'] and 'name' in data['data']['city']:
                result['station'] = data['data']['city']['name']
            
            if 'time' in data['data'] and 'iso' in data['data']['time']:
                result['time'] = data['data']['time']['iso']
            
            logger.info(f"Successfully retrieved AQI data for {city_name}: AQI {result['aqi']}")
            return result
        else:
            logger.warning(f"AQICN API returned non-OK status for {city_name}: {data['status']}")
            return None
    except Exception as e:
        logger.error(f"Error getting air quality data for {city_name}: {e}")
        return None
        
def get_aqi_category(aqi_value):
    """Get AQI category based on value"""
    if aqi_value <= 50:
        return "Good"
    elif aqi_value <= 100:
        return "Moderate"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi_value <= 200:
        return "Unhealthy"
    elif aqi_value <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def get_india_air_quality_map_data():
    """
    Get air quality data for all stations in India
    
    Returns:
        list: List of air quality stations with coordinates and AQI values
    """
    try:
        # Check if cached data exists
        cache_file = 'frontend/static/data/cache/india_aqi_data.json'
        if os.path.exists(cache_file):
            # Get file modification time
            mod_time = os.path.getmtime(cache_file)
            now = datetime.now().timestamp()
            
            # If file is less than 1 hour old, use cached data
            if now - mod_time < 3600:  # 1 hour in seconds
                with open(cache_file, 'r') as f:
                    logger.info("Using cached India AQI data")
                    return json.load(f)
        
        # Mock data for demonstration
        # In a real implementation, this would fetch data from an API
        with open('frontend/static/data/marker_data.json', 'r') as f:
            marker_data = json.load(f)
        
        # Filter for India
        india_data = [m for m in marker_data if m.get('Country') == 'India']
        
        # Save to cache
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(india_data, f)
            
        return india_data
    except Exception as e:
        logger.error(f"Error getting India air quality map data: {e}")
        return []

def get_global_air_quality_map_data():
    """
    Get global air quality data
    """
    try:
        # Try to use AQICN API
        url = f"{AQICN_BASE_URL}/map/bounds/?latlng=-90,-180,90,180&token={AQICN_API_KEY}"
        
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
        except Exception as req_error:
            logger.error(f"Error connecting to AQICN API: {req_error}")
            # Fall back to static data
            with open('frontend/static/data/marker_data.json', 'r') as f:
                return json.load(f)
        
        if data.get('status') == 'ok' and 'data' in data and len(data['data']) > 0:
            # Transform the data to match our expected format
            markers = []
            for station in data['data']:
                try:
                    # Skip entries without AQI or coordinates
                    if 'aqi' not in station or 'lat' not in station or 'lon' not in station:
                        continue
                        
                    if not station.get('station', {}).get('name'):
                        continue
                        
                    # Make sure AQI is a number
                    aqi_value = 0
                    try:
                        aqi_value = float(station['aqi']) if station['aqi'] not in ['-', '', None] else 0
                    except (ValueError, TypeError):
                        continue  # Skip stations with invalid AQI values
                    
                    # Parse location
                    location_parts = station['station']['name'].split(',')
                    city = location_parts[0].strip()
                    country = location_parts[-1].strip() if len(location_parts) > 1 else "Unknown"
                    
                    # Determine AQI category and color
                    category, color = get_aqi_category_and_color(aqi_value)
                    
                    # Simplify country names
                    if country.lower().startswith("united states"):
                        country = "United States of America"
                    elif country.lower() == "united kingdom":
                        country = "United Kingdom"
                    
                    # Try to determine continent
                    from data_processing import get_continent_for_country
                    continent = get_continent_for_country(country)
                    
                    # Create marker with expected fields
                    marker = {
                        "AQI": aqi_value,
                        "AQI_Category": category,
                        "City": city,
                        "Country": country,
                        "Continent": continent,
                        "Latitude": float(station['lat']),
                        "Longitude": float(station['lon']),
                        "color": color,
                        "time": station.get('station', {}).get('time', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    }
                    markers.append(marker)
                except Exception as e:
                    # Skip invalid entries
                    logger.debug(f"Skipping invalid entry: {e}")
                    continue
            
            if len(markers) > 0:
                # Cache the results for future use
                save_map_data_to_cache(markers)
                logger.info(f"Successfully fetched {len(markers)} air quality measurements from AQICN")
                return markers
                
        # If we couldn't get data from AQICN, fall back to static data
        logger.warning("Failed to fetch global air quality map data, falling back to static data")
        with open('frontend/static/data/marker_data.json', 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error getting global air quality map data: {e}")
        # Fall back to static data
        try:
            with open('frontend/static/data/marker_data.json', 'r') as f:
                return json.load(f)
        except:
            return []

def get_aqi_category_and_color(aqi_value):
    """
    Determine AQI category and color based on AQI value
    
    Args:
        aqi_value (float): AQI value
        
    Returns:
        tuple: (category, color)
    """
    if aqi_value <= 50:
        return ("Good", "#009966")
    elif aqi_value <= 100:
        return ("Moderate", "#ffde33")
    elif aqi_value <= 150:
        return ("Unhealthy for Sensitive Groups", "#ff9933")
    elif aqi_value <= 200:
        return ("Unhealthy", "#cc0033")
    elif aqi_value <= 300:
        return ("Very Unhealthy", "#660099")
    else:
        return ("Hazardous", "#7e0023")

def save_map_data_to_cache(data):
    """
    Save map data to a cache file
    
    Args:
        data (list): List of marker data
    """
    try:
        cache_file = 'frontend/static/data/cache/map_data_cache.json'
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(data, f)
        logger.info(f"Saved {len(data)} markers to cache")
    except Exception as e:
        logger.error(f"Error saving map data to cache: {e}")

def get_cached_map_data():
    """
    Get cached map data
    
    Returns:
        list: List of marker data
    """
    try:
        cache_file = 'frontend/static/data/cache/map_data_cache.json'
        if os.path.exists(cache_file):
            # Get file modification time
            mod_time = os.path.getmtime(cache_file)
            now = datetime.now().timestamp()
            
            # If file is less than 1 hour old, use cached data
            if now - mod_time < 3600:  # 1 hour in seconds
                with open(cache_file, 'r') as f:
                    logger.info("Using cached map data")
                    return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error getting cached map data: {e}")
        return []

def get_station_weather_data(station_id):
    """
    Get weather data for a station
    
    Args:
        station_id (str): Station ID
        
    Returns:
        dict: Weather data including wind speed, direction, and temperature
    """
    try:
        # Mock data structure for demonstration
        return {
            "station_id": station_id,
            "temperature": 25.5,
            "humidity": 65,
            "pressure": 1013,
            "wind": {
                "speed": 12,
                "direction": 270
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting weather data for station {station_id}: {e}")
        return None

# IQAir API functions
def get_iqair_countries():
    """
    Get list of countries supported by IQAir API
    
    Returns:
        list: List of countries
    """
    try:
        url = f"{IQAIR_API_URL}/countries?key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            countries = [country for country in data['data']]
            return countries
        else:
            logger.warning(f"Failed to fetch countries from IQAir: {data.get('message')}")
            # Fall back to static list
            return [
                "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
                "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
                "Bahrain", "Bangladesh", "Belgium", "Bolivia", "Bosnia and Herzegovina",
                "Brazil", "Bulgaria", "Cambodia", "Canada", "Chile",
                "China", "Colombia", "Croatia", "Cyprus", "Czech Republic",
                "Denmark", "Ecuador", "Egypt", "Estonia", "Finland",
                "France", "Georgia", "Germany", "Ghana", "Greece",
                "Hong Kong", "Hungary", "Iceland", "India", "Indonesia",
                "Iran", "Iraq", "Ireland", "Israel", "Italy",
                "Japan", "Jordan", "Kazakhstan", "Kenya", "Kosovo",
                "Kuwait", "Kyrgyzstan", "Latvia", "Lebanon", "Lithuania",
                "Luxembourg", "Malaysia", "Malta", "Mexico", "Moldova",
                "Mongolia", "Montenegro", "Morocco", "Myanmar", "Nepal",
                "Netherlands", "New Zealand", "Nigeria", "North Macedonia", "Norway",
                "Oman", "Pakistan", "Peru", "Philippines", "Poland",
                "Portugal", "Qatar", "Romania", "Russia", "Saudi Arabia",
                "Serbia", "Singapore", "Slovakia", "Slovenia", "South Africa",
                "South Korea", "Spain", "Sri Lanka", "Sweden", "Switzerland",
                "Taiwan", "Thailand", "Turkey", "Uganda", "Ukraine",
                "United Arab Emirates", "United Kingdom", "United States", "Uzbekistan", "Vietnam"
            ]
    except Exception as e:
        logger.error(f"Error getting IQAir countries: {e}")
        return []

def get_iqair_states(country):
    """
    Get list of states/regions for a country supported by IQAir API
    
    Args:
        country (str): Country name
        
    Returns:
        list: List of states/regions
    """
    try:
        url = f"{IQAIR_API_URL}/states?country={country}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            states = [state for state in data['data']]
            return states
        else:
            logger.warning(f"Failed to fetch states from IQAir: {data.get('message')}")
            # Fall back to static data
            states_by_country = {
                "United States": [
                    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
                    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
                    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
                    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
                    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
                    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
                    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
                    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
                    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
                    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
                ],
                "India": [
                    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                    "Uttar Pradesh", "Uttarakhand", "West Bengal"
                ],
                "China": [
                    "Anhui", "Beijing", "Chongqing", "Fujian", "Gansu",
                    "Guangdong", "Guangxi", "Guizhou", "Hainan", "Hebei",
                    "Heilongjiang", "Henan", "Hong Kong", "Hubei", "Hunan",
                    "Inner Mongolia", "Jiangsu", "Jiangxi", "Jilin", "Liaoning",
                    "Macau", "Ningxia", "Qinghai", "Shaanxi", "Shandong",
                    "Shanghai", "Shanxi", "Sichuan", "Tianjin", "Tibet",
                    "Xinjiang", "Yunnan", "Zhejiang"
                ]
            }
            
            return states_by_country.get(country, [])
    except Exception as e:
        logger.error(f"Error getting IQAir states for {country}: {e}")
        return []

def get_iqair_cities(country, state):
    """
    Get list of cities for a state/region supported by IQAir API
    
    Args:
        country (str): Country name
        state (str): State/region name
        
    Returns:
        list: List of cities
    """
    try:
        url = f"{IQAIR_API_URL}/cities?country={country}&state={state}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            cities = [city for city in data['data']]
            return cities
        else:
            logger.warning(f"Failed to fetch cities from IQAir: {data.get('message')}")
            # Fall back to static data
            cities_by_state = {
                "California": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "Fresno"],
                "New York": ["New York City", "Buffalo", "Rochester", "Albany", "Syracuse"],
                "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik"],
                "Delhi": ["New Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"],
                "Beijing": ["Dongcheng", "Xicheng", "Chaoyang", "Haidian", "Fengtai"]
            }
            
            return cities_by_state.get(state, [])
    except Exception as e:
        logger.error(f"Error getting IQAir cities for {state}, {country}: {e}")
        return []

def get_iqair_city_data(country, state, city):
    """
    Get air quality data for a specific city using IQAir API
    
    Args:
        country (str): Country name
        state (str): State/region name
        city (str): City name
        
    Returns:
        dict: Air quality data for the city
    """
    try:
        url = f"{IQAIR_API_URL}/city?country={country}&state={state}&city={city}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            result = {
                "city": city,
                "state": state,
                "country": country,
                "timestamp": datetime.now().isoformat()
            }
            
            # Extract AQI
            aqicn = data['data'].get('current', {}).get('pollution', {})
            if aqicn:
                result['aqi'] = {
                    "value": aqicn.get('aqius'),
                    "category": get_aqi_category(aqicn.get('aqius', 0))
                }
                result['pollutants'] = {
                    "pm25": {
                        "value": aqicn.get('pm25', 0),
                        "category": get_aqi_category(aqicn.get('pm25', 0))
                    },
                    "pm10": {
                        "value": aqicn.get('pm10', 0),
                        "category": get_aqi_category(aqicn.get('pm10', 0))
                    }
                }
            
            # Extract weather
            weather = data['data'].get('current', {}).get('weather', {})
            if weather:
                result['weather'] = {
                    "temperature": weather.get('tp'),
                    "humidity": weather.get('hu'),
                    "pressure": weather.get('pr'),
                    "wind_speed": weather.get('ws'),
                    "wind_direction": weather.get('wd')
                }
                
            return result
        else:
            logger.warning(f"Failed to fetch city data from IQAir: {data.get('message')}")
            # Fall back to mock data
            return {
                "city": city,
                "state": state,
                "country": country,
                "aqi": {
                    "value": 85,
                    "category": "Moderate"
                },
                "pollutants": {
                    "pm25": {
                        "value": 20.5,
                        "category": "Moderate"
                    },
                    "pm10": {
                        "value": 35.2,
                        "category": "Good"
                    },
                    "o3": {
                        "value": 42.1,
                        "category": "Good"
                    },
                    "no2": {
                        "value": 18.3,
                        "category": "Good"
                    }
                },
                "weather": {
                    "temperature": 25.5,
                    "humidity": 65,
                    "pressure": 1013,
                    "wind_speed": 12,
                    "wind_direction": 270
                },
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting IQAir data for {city}, {state}, {country}: {e}")
        return None

def get_iqair_nearest_city(lat, lon):
    """
    Get air quality data for the nearest city using IQAir API
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Air quality data for the nearest city
    """
    try:
        url = f"{IQAIR_API_URL}/nearest_city?lat={lat}&lon={lon}&key={IQAIR_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            city_data = data['data']
            result = {
                "city": city_data.get('city'),
                "state": city_data.get('state'),
                "country": city_data.get('country'),
                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Extract AQI
            aqicn = city_data.get('current', {}).get('pollution', {})
            if aqicn:
                result['aqi'] = {
                    "value": aqicn.get('aqius'),
                    "category": get_aqi_category(aqicn.get('aqius', 0))
                }
                result['pollutants'] = {
                    "pm25": {
                        "value": aqicn.get('pm25', 0),
                        "category": get_aqi_category(aqicn.get('pm25', 0))
                    },
                    "pm10": {
                        "value": aqicn.get('pm10', 0),
                        "category": get_aqi_category(aqicn.get('pm10', 0))
                    }
                }
            
            # Extract weather
            weather = city_data.get('current', {}).get('weather', {})
            if weather:
                result['weather'] = {
                    "temperature": weather.get('tp'),
                    "humidity": weather.get('hu'),
                    "pressure": weather.get('pr'),
                    "wind_speed": weather.get('ws'),
                    "wind_direction": weather.get('wd')
                }
                
            return result
        else:
            logger.warning(f"Failed to fetch nearest city data from IQAir: {data.get('message')}")
            # Fall back to mock data
            return {
                "city": "Nearest City",
                "state": "State",
                "country": "Country",
                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                },
                "aqi": {
                    "value": 65,
                    "category": "Moderate"
                },
                "pollutants": {
                    "pm25": {
                        "value": 15.2,
                        "category": "Moderate"
                    },
                    "pm10": {
                        "value": 28.5,
                        "category": "Good"
                    },
                    "o3": {
                        "value": 35.8,
                        "category": "Good"
                    },
                    "no2": {
                        "value": 12.7,
                        "category": "Good"
                    }
                },
                "weather": {
                    "temperature": 22.3,
                    "humidity": 58,
                    "pressure": 1012,
                    "wind_speed": 8,
                    "wind_direction": 225
                },
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting IQAir nearest city data for ({lat}, {lon}): {e}")
        return None

def get_iqair_nearest_station(lat, lon):
    """
    Get air quality data for the nearest station using IQAir API
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Air quality data for the nearest station
    """
    try:
        # Mock data structure for demonstration
        return {
            "station": "Nearest Station",
            "station_id": "ST12345",
            "coordinates": {
                "latitude": lat,
                "longitude": lon
            },
            "aqi": {
                "value": 55,
                "category": "Moderate"
            },
            "pollutants": {
                "pm25": {
                    "value": 12.8,
                    "category": "Moderate"
                },
                "pm10": {
                    "value": 22.1,
                    "category": "Good"
                },
                "o3": {
                    "value": 32.5,
                    "category": "Good"
                },
                "no2": {
                    "value": 11.2,
                    "category": "Good"
                }
            },
            "weather": {
                "temperature": 21.8,
                "humidity": 62,
                "pressure": 1010,
                "wind_speed": 7,
                "wind_direction": 210
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting IQAir nearest station data for ({lat}, {lon}): {e}")
        return None