import os
import logging
import json
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd

import data_processing
import api_utils

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# Load data files
try:
    # Load marker data for the map
    with open('static/data/marker_data.json', 'r') as f:
        marker_data = json.load(f)

    # Load countries data
    with open('static/data/countries_data.json', 'r') as f:
        countries_data = json.load(f)

    # Load cities monthly data
    with open('static/data/cities_monthly_data.json', 'r') as f:
        cities_monthly_data = json.load(f)

    logger.info("Successfully loaded data files")
except Exception as e:
    logger.error(f"Error loading data files: {e}")
    marker_data = []
    countries_data = []
    cities_monthly_data = []

# API info endpoint
@app.route('/api')
def api_info():
    return jsonify({
        "name": "Air Quality Dashboard API",
        "version": "1.0.0",
        "description": "API endpoints for Air Quality Dashboard",
        "endpoints": [
            "/api/dashboard/data",
            "/api/map/data",
            "/api/most-polluted/data",
            "/api/aqi-csv-data",
            "/api/heatmap-data",
            "/api/india-aqi-data",
            "/api/global-air-quality-map-data",
            "/api/interactive-map-data",
            "/api/city-aqi/<city_name>",
            "/api/country-data/<country>",
            "/api/city-data/<city>/<state>",
            "/api/cities-for-comparison",
            "/api/city-comparison-data",
            "/api/cities/<country>"
        ]
    })

# Root endpoint - serve frontend
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

# Dashboard data endpoint
@app.route('/api/dashboard/data')
def dashboard_data():
    # Calculate global average AQI with error handling
    valid_aqi_values = [c.get('2024', 0) for c in countries_data if c.get('2024') is not None and isinstance(c.get('2024'), (int, float))]
    global_avg_aqi = sum(valid_aqi_values) / len(valid_aqi_values) if valid_aqi_values else 45  # Default value if no valid data

    # Filter out countries with invalid AQI values
    valid_countries = [c for c in countries_data if c.get('2024') is not None and isinstance(c.get('2024'), (int, float)) and c.get('Country') is not None]
    
    # Get top 10 most polluted countries with valid data
    top_polluted_countries = sorted(valid_countries, key=lambda x: x.get('2024', 0), reverse=True)[:10]
    
    # Count countries with monitoring
    monitored_countries_count = len(set([c.get('Country') for c in valid_countries if c.get('Country')]))

    return jsonify({
        'global_avg_aqi': global_avg_aqi,
        'top_polluted_countries': top_polluted_countries,
        'monitored_countries_count': monitored_countries_count,
        'timestamp': datetime.now().isoformat()
    })

# Map data endpoint
@app.route('/api/map/data')
def map_data():
    # Get unique continents, countries, and cities for filters
    continents = sorted([str(m.get('Continent', 'Unknown')) for m in marker_data if 'Continent' in m and m.get('Continent') is not None])
    continents = sorted(list(set(continents)))
    
    countries = [str(m.get('Country', 'Unknown')) for m in marker_data if 'Country' in m and m.get('Country') is not None]
    countries = sorted(list(set(countries)))
    
    cities = [str(m.get('City', 'Unknown')) for m in marker_data if 'City' in m and m.get('City') is not None]
    cities = sorted(list(set(cities)))

    return jsonify({
        'markers': marker_data[:100],  # Limit to 100 markers for performance
        'continents': continents,
        'countries': countries,
        'cities': cities[:500],  # Limit to 500 cities for performance
        'timestamp': datetime.now().isoformat()
    })

# Most polluted data endpoint
@app.route('/api/most-polluted/data')
def most_polluted_data():
    # Get top 50 most polluted countries
    top_polluted_countries = sorted(countries_data, key=lambda x: x.get('2024', 0), reverse=True)[:50]

    # Get cities with monthly data for states
    cities_with_states = []
    if cities_monthly_data:
        for city_data in cities_monthly_data:
            if 'City' in city_data and 'State' in city_data:
                cities_with_states.append({
                    'city': city_data['City'],
                    'state': city_data['State']
                })

    return jsonify({
        'top_polluted_countries': top_polluted_countries,
        'cities_with_states': cities_with_states[:100],  # Limit to 100 cities for performance
        'timestamp': datetime.now().isoformat()
    })

# AQI CSV data endpoint
@app.route('/api/aqi-csv-data')
def aqi_csv_data():
    """
    API endpoint to get processed AQI CSV data
    """
    try:
        # Path to the CSV file
        csv_file_path = 'static/data/AQI and Lat Long of Countries.csv'
        
        # Read the CSV file using pandas
        df = pd.read_csv(csv_file_path)
        
        # Group by country and calculate average AQI
        country_avg = df.groupby('Country')['AQI Value'].mean().reset_index()
        country_avg = country_avg.sort_values('AQI Value', ascending=False)
        
        # Get top 20 countries with highest AQI values
        top_countries = country_avg.head(20).to_dict('records')
        
        # Group by city and get top 20 cities with highest AQI values
        city_data = df.drop_duplicates(subset=['City', 'Country'])
        city_data = city_data.sort_values('AQI Value', ascending=False)
        top_cities = city_data.head(20)[['City', 'Country', 'AQI Value', 'AQI Category']].to_dict('records')
        
        # Get cleanest cities (lowest AQI)
        cleanest_cities = city_data.sort_values('AQI Value').head(10)[['City', 'Country', 'AQI Value', 'AQI Category']].to_dict('records')
        
        # Get data for the heatmap
        heatmap_data = df[['lat', 'lng', 'AQI Value', 'City', 'Country']].rename(
            columns={'lat': 'lat', 'lng': 'lng', 'AQI Value': 'value'}
        ).to_dict('records')
        
        # Calculate distribution by category
        category_counts = df['AQI Category'].value_counts().to_dict()
        
        return jsonify({
            'top_countries': top_countries,
            'top_cities': top_cities,
            'cleanest_cities': cleanest_cities,
            'heatmap_data': heatmap_data[:100],  # Limit to 100 items for performance
            'category_counts': category_counts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error processing CSV data: {e}")
        return jsonify({
            'error': str(e)
        }), 500

# Heatmap data endpoint
@app.route('/api/heatmap-data')
def heatmap_data():
    try:
        df = pd.read_csv('static/data/updated_polluted_cities_monthly_with_states.csv')
        data = []
        for _, row in df.iterrows():
            monthly_avg = sum(float(row[month]) for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'] 
                            if str(row[month]) != '--') / 12
            data.append({
                'city': row['City'],
                'state': row['State'],
                'value': monthly_avg
            })
        return jsonify(data[:100])  # Limit to 100 items for performance
    except Exception as e:
        logger.error(f"Error getting heatmap data: {e}")
        return jsonify({"error": str(e)}), 500

# India AQI data endpoint
@app.route('/api/india-aqi-data')
def india_aqi_data():
    """
    API endpoint to get real-time air quality data for India
    """
    try:
        # Get air quality data for all stations in India
        india_data = api_utils.get_india_air_quality_map_data()
        return jsonify(india_data[:100])  # Limit to 100 items for performance
    except Exception as e:
        logger.error(f"Error getting India AQI data: {e}")
        return jsonify({"error": str(e)}), 500

# City AQI data endpoint
@app.route('/api/city-aqi/<city_name>')
def city_aqi(city_name):
    """
    API endpoint to get real-time air quality data for a specific city
    """
    try:
        # Get air quality data for the specified city
        city_data = api_utils.get_city_air_quality(city_name)
        if city_data:
            return jsonify(city_data)
        else:
            return jsonify({"error": f"No data found for city '{city_name}'"}), 404
    except Exception as e:
        logger.error(f"Error getting city AQI data for {city_name}: {e}")
        return jsonify({"error": str(e)}), 500

# Global air quality map data endpoint
@app.route('/api/global-air-quality-map-data')
def global_air_quality_map_data():
    """
    API endpoint to get global air quality data
    """
    try:
        # Get global air quality data
        global_data = api_utils.get_global_air_quality_map_data()
        return jsonify(global_data[:100])  # Limit to 100 items for performance
    except Exception as e:
        logger.error(f"Error getting global AQI data: {e}")
        return jsonify({"error": str(e)}), 500

# Interactive map data endpoint
@app.route('/api/interactive-map-data')
def interactive_map_data():
    """
    API endpoint to get data for the interactive map with detailed markers
    """
    try:
        # Try to get cached data first
        cached_data = api_utils.get_cached_map_data()
        if cached_data and len(cached_data) > 0:
            logger.info(f"Using cached map data with {len(cached_data)} markers")
            return jsonify(cached_data[:100])  # Limit to 100 items for performance
            
        # If no cached data, get global data
        global_data = api_utils.get_global_air_quality_map_data()
        if global_data and len(global_data) > 0:
            logger.info(f"Using fresh global data with {len(global_data)} markers")
            return jsonify(global_data[:100])  # Limit to 100 items for performance
            
        # Fallback to static marker data
        logger.warning("Using static marker data as fallback")
        return jsonify(marker_data[:100])  # Limit to 100 items for performance
    except Exception as e:
        logger.error(f"Error getting interactive map data: {e}")
        return jsonify({"error": str(e)}), 500

# Country data endpoint
@app.route('/api/country-data/<country>')
def country_data(country):
    try:
        country_data = None
        
        # Find country in the loaded data
        for c in countries_data:
            if c.get('Country') == country:
                country_data = c
                break
                
        if not country_data:
            return jsonify({"error": f"Country '{country}' not found"}), 404
            
        # Get monthly data for charting
        monthly_data = [country_data.get(month, 0) for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]
        
        result = {
            "name": country_data.get('Country'),
            "rank": country_data.get('Rank', 0),
            "avg_aqi": country_data.get('2024', 0),
            "monthly_data": monthly_data,
            "months": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting country data for {country}: {e}")
        return jsonify({"error": str(e)}), 500

# City data endpoint
@app.route('/api/city-data/<path:city_state>')
def city_data(city_state):
    try:
        parts = city_state.split('/')
        if len(parts) != 2:
            return jsonify({"error": "City data must be requested as city/state"}), 400
            
        city = parts[0]
        state = parts[1]
        
        city_data = None
        
        # Find city in the loaded data
        for c in cities_monthly_data:
            if c.get('City') == city and c.get('State') == state:
                city_data = c
                break
                
        if not city_data:
            return jsonify({"error": f"City '{city}, {state}' not found"}), 404
            
        # Get monthly data for charting
        monthly_data = [city_data.get(month, 0) for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]
        
        result = {
            "name": city_data.get('City'),
            "state": city_data.get('State'),
            "country": city_data.get('Country'),
            "monthly_data": monthly_data,
            "months": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting city data for {city_state}: {e}")
        return jsonify({"error": str(e)}), 500

# Cities for comparison endpoint
@app.route('/api/cities-for-comparison')
def cities_for_comparison():
    """
    API endpoint to get cities data for comparison charts
    """
    try:
        # Use pandas to read and process the CSV
        df = pd.read_csv('static/data/updated_polluted_cities_monthly_with_states.csv')
        
        # Process each row into the format we need
        cities_data = []
        for _, row in df.iterrows():
            city_data = process_city_data(row)
            if city_data:
                cities_data.append(city_data)
                
        return jsonify(cities_data[:100])  # Limit to 100 items for performance
    except Exception as e:
        logger.error(f"Error getting cities for comparison: {e}")
        return jsonify([]), 500

# Helper function to process city data from CSV
def process_city_data(row):
    """Helper function to process a city row from the CSV file"""
    try:
        city_name = row.get('City', '')
        state_name = row.get('State', '')
        
        if not city_name or not state_name:
            return None
            
        # Extract monthly AQI values
        monthly_values = []
        for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
            value = row.get(month)
            # Handle missing or non-numeric values
            if value == '--' or pd.isna(value):
                monthly_values.append(None)
            else:
                try:
                    monthly_values.append(float(value))
                except (ValueError, TypeError):
                    monthly_values.append(None)
                    
        # Calculate average of available values
        valid_values = [v for v in monthly_values if v is not None]
        avg_aqi = sum(valid_values) / len(valid_values) if valid_values else None
        
        return {
            'city': city_name,
            'state': state_name,
            'display': f"{city_name}, {state_name}",
            'monthly_values': monthly_values,
            'avg_aqi': avg_aqi
        }
    except Exception as e:
        logger.error(f"Error processing city data: {e}")
        return None

# City comparison data endpoint
@app.route('/api/city-comparison-data')
def city_comparison_data():
    """
    API endpoint to get detailed comparison data for two specific cities
    """
    city1 = request.args.get('city1')
    city2 = request.args.get('city2')
    
    if not city1 or not city2:
        return jsonify({'error': 'Both city1 and city2 parameters are required'}), 400
        
    try:
        # Split city and state
        city1_parts = city1.split(', ')
        city2_parts = city2.split(', ')
        
        if len(city1_parts) < 2 or len(city2_parts) < 2:
            return jsonify({'error': 'Cities must be in format "City, State"'}), 400
            
        city1_name = city1_parts[0]
        city1_state = city1_parts[1]
        city2_name = city2_parts[0]
        city2_state = city2_parts[1]
        
        # Use pandas to read and process the CSV
        df = pd.read_csv('static/data/updated_polluted_cities_monthly_with_states.csv')
        
        # Find the two cities
        city1_data = df[(df['City'] == city1_name) & (df['State'] == city1_state)]
        city2_data = df[(df['City'] == city2_name) & (df['State'] == city2_state)]
        
        if city1_data.empty or city2_data.empty:
            return jsonify({'error': 'One or both cities not found'}), 404
            
        # Process each city's data
        city1_processed = process_city_data(city1_data.iloc[0])
        city2_processed = process_city_data(city2_data.iloc[0])
        
        # Get month labels
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        
        result = {
            'city1': city1_processed,
            'city2': city2_processed,
            'months': months
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error comparing cities: {e}")
        return jsonify({'error': str(e)}), 500

# Cities for country endpoint
@app.route('/api/cities/<country>')
def cities_for_country(country):
    """
    API endpoint to get cities for a specific country from our dataset
    """
    try:
        # Get cities from marker data
        cities = []
        
        # Case-insensitive country matching
        country_markers = [m for m in marker_data if str(m.get('Country', '')).lower() == country.lower()]
        
        # Extract unique city names
        for marker in country_markers:
            if 'City' in marker and marker['City'] not in cities:
                cities.append(marker['City'])
        
        # Sort cities alphabetically
        cities.sort()
        
        return jsonify(cities)
    except Exception as e:
        logger.error(f"Error getting cities for country {country}: {e}")
        return jsonify([]), 500

# Frontend routes to serve static files
@app.route('/frontend/<path:path>')
def serve_frontend_files(path):
    """Serve frontend files from the frontend directory"""
    return send_from_directory('frontend', path)

# Serve static JS/CSS files directly
@app.route('/app.js')
def serve_app_js():
    return send_from_directory('frontend', 'app.js')

@app.route('/map.js')
def serve_map_js():
    return send_from_directory('frontend', 'map.js')

@app.route('/styles.css')
def serve_styles_css():
    return send_from_directory('frontend', 'styles.css')

# Redirect root to frontend
@app.route('/web')
def web_index():
    return send_from_directory('frontend', 'index.html')

@app.route('/web/map')
def web_map():
    return send_from_directory('frontend', 'map.html')

@app.route('/web/api-test')
def web_api_test():
    return send_from_directory('frontend', 'api_test.html')

# Start the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
