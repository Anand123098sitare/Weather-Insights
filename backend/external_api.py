"""
Module for external API integrations and data fetching
"""
import os
import logging
import time
import json
import requests
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# API Key for IQAir API
API_KEY = "3dc447e982a5cc571500f0747d43eb0e7f095a62"

# Base URLs for APIs
IQAIR_BASE_URL = "https://api.airvisual.com/v2"

def get_countries():
    """Get list of supported countries from IQAir API"""
    url = f"{IQAIR_BASE_URL}/countries?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', [])
            else:
                logger.error(f"IQAir API error: {data.get('data', {}).get('message')}")
                return []
        else:
            logger.error(f"IQAir API request failed with status: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching countries from IQAir API: {e}")
        return []

def get_states(country):
    """Get list of states/regions for a country from IQAir API"""
    url = f"{IQAIR_BASE_URL}/states?country={country}&key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', [])
            else:
                logger.error(f"IQAir API error: {data.get('data', {}).get('message')}")
                return []
        else:
            logger.error(f"IQAir API request failed with status: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching states for {country} from IQAir API: {e}")
        return []

def get_cities(country, state):
    """Get list of cities for a state/region from IQAir API"""
    url = f"{IQAIR_BASE_URL}/cities?state={state}&country={country}&key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', [])
            else:
                logger.error(f"IQAir API error: {data.get('data', {}).get('message')}")
                return []
        else:
            logger.error(f"IQAir API request failed with status: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching cities for {state}, {country} from IQAir API: {e}")
        return []

def get_city_data(country, state, city):
    """Get air quality data for a specific city from IQAir API"""
    url = f"{IQAIR_BASE_URL}/city?city={city}&state={state}&country={country}&key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', {})
            else:
                logger.error(f"IQAir API error: {data.get('data', {}).get('message')}")
                return {}
        else:
            logger.error(f"IQAir API request failed with status: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching data for {city}, {state}, {country} from IQAir API: {e}")
        return {}

def get_nearest_city(lat, lon):
    """Get air quality data for the nearest city from IQAir API"""
    url = f"{IQAIR_BASE_URL}/nearest_city?lat={lat}&lon={lon}&key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', {})
            else:
                logger.error(f"IQAir API error: {data.get('data', {}).get('message')}")
                return {}
        else:
            logger.error(f"IQAir API request failed with status: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching nearest city data from IQAir API: {e}")
        return {}

def fetch_realtime_data_for_countries(country_list, cache_duration=3600):
    """
    Fetch real-time air quality data for a list of countries
    
    Args:
        country_list (list): List of country names
        cache_duration (int): Duration in seconds to cache the data (default: 1 hour)
        
    Returns:
        dict: Real-time data for all countries
    """
    cache_file = 'frontend/static/data/cache/realtime_countries_data.json'
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    
    # Check if cache exists and is fresh
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                
            if cached_data.get('timestamp'):
                cache_time = cached_data.get('timestamp')
                current_time = time.time()
                if current_time - cache_time < cache_duration:
                    logger.info(f"Using cached realtime country data (age: {int((current_time - cache_time) / 60)} minutes)")
                    return cached_data.get('data', {})
        except Exception as e:
            logger.error(f"Error reading cache file: {e}")
    
    # Fetch fresh data
    result = {}
    for country in country_list:
        try:
            # Get major cities for each country
            cities_data = []
            states = get_states(country)
            if states:
                # For simplicity, get cities from the first state
                for state_data in states[:2]:  # Limit to first 2 states to avoid API rate limits
                    state = state_data.get('state')
                    cities = get_cities(country, state)
                    if cities:
                        # For simplicity, get data from the first city
                        for city_data in cities[:3]:  # Limit to first 3 cities to avoid API rate limits
                            city = city_data.get('city')
                            city_aqi = get_city_data(country, state, city)
                            if city_aqi and city_aqi.get('current'):
                                cities_data.append({
                                    'city': city,
                                    'state': state,
                                    'aqi': city_aqi.get('current', {}).get('pollution', {}).get('aqius'),
                                    'timestamp': datetime.now().isoformat()
                                })
            
            # Calculate country average from cities
            if cities_data:
                avg_aqi = sum(city.get('aqi', 0) for city in cities_data) / len(cities_data)
                result[country] = {
                    'aqi': int(avg_aqi),
                    'cities': cities_data,
                    'timestamp': datetime.now().isoformat()
                }
                # Wait to avoid API rate limiting
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error processing country {country}: {e}")
    
    # Cache the results
    try:
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'data': result
            }, f)
        logger.info(f"Cached realtime data for {len(result)} countries")
    except Exception as e:
        logger.error(f"Error writing cache file: {e}")
    
    return result

def merge_csv_with_realtime_data():
    """
    Merge the CSV data with real-time API data for a comprehensive dataset
    
    Returns:
        DataFrame: Merged data
    """
    # Read the CSV file
    csv_file = 'frontend/static/data/world_most_polluted_countries_2024.csv'
    try:
        df = pd.read_csv(csv_file)
        
        # Extract country names from the CSV
        countries = df['Country'].tolist()
        
        # Get realtime data for countries in the CSV
        realtime_data = fetch_realtime_data_for_countries(countries)
        
        # Add realtime data to the DataFrame
        df['Realtime_AQI'] = df['Country'].apply(
            lambda country: realtime_data.get(country, {}).get('aqi', None)
        )
        
        # Add a timestamp for the realtime data
        df['Realtime_Timestamp'] = datetime.now().isoformat()
        
        return df
    except Exception as e:
        logger.error(f"Error merging CSV with realtime data: {e}")
        return None

def export_enhanced_data():
    """
    Export the enhanced data (CSV + realtime) to a JSON file
    
    Returns:
        bool: Success status
    """
    try:
        df = merge_csv_with_realtime_data()
        if df is not None:
            # Convert to JSON and save
            result = df.to_dict(orient='records')
            
            output_file = 'frontend/static/data/enhanced_country_data.json'
            with open(output_file, 'w') as f:
                json.dump(result, f)
            
            logger.info(f"Enhanced data exported to {output_file}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error exporting enhanced data: {e}")
        return False
        
def get_global_air_quality_summary():
    """
    Get a global air quality summary based on the enhanced dataset
    
    Returns:
        dict: Global AQI summary statistics
    """
    try:
        # Read the enhanced data if available
        json_file = 'frontend/static/data/enhanced_country_data.json'
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
        else:
            # Fall back to CSV data
            df = pd.read_csv('frontend/static/data/world_most_polluted_countries_2024.csv')
            data = df.to_dict(orient='records')
        
        # Calculate statistics
        avg_values = [float(d.get('2024 Avg', 0)) for d in data if d.get('2024 Avg') is not None]
        if not avg_values:
            return {}
            
        # Create AQI categories
        categories = {
            'Good (0-50)': 0,
            'Moderate (51-100)': 0,
            'Unhealthy for Sensitive Groups (101-150)': 0,
            'Unhealthy (151-200)': 0,
            'Very Unhealthy (201-300)': 0,
            'Hazardous (301+)': 0
        }
        
        for aqi in avg_values:
            if aqi <= 50:
                categories['Good (0-50)'] += 1
            elif aqi <= 100:
                categories['Moderate (51-100)'] += 1
            elif aqi <= 150:
                categories['Unhealthy for Sensitive Groups (101-150)'] += 1
            elif aqi <= 200:
                categories['Unhealthy (151-200)'] += 1
            elif aqi <= 300:
                categories['Very Unhealthy (201-300)'] += 1
            else:
                categories['Hazardous (301+)'] += 1
        
        # Return summary
        return {
            'global_avg_aqi': sum(avg_values) / len(avg_values),
            'max_aqi': max(avg_values),
            'min_aqi': min(avg_values),
            'total_countries': len(data),
            'countries_with_data': len(avg_values),
            'categories': categories,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating global summary: {e}")
        return {}

if __name__ == "__main__":
    # For testing
    export_enhanced_data()