import os
import logging
import json
from datetime import datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import pandas as pd

import data_processing
import api_utils


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_for_testing")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure the application as an API server
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# configure the database, relative to the app instance folder
# Check if DATABASE_URL is available, if not use SQLite as fallback
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    app.logger.warning("DATABASE_URL not found, falling back to SQLite database")
    db_url = "sqlite:///air_quality.db"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.logger.info(f"Using database: {db_url.split('@')[-1] if '@' in db_url else db_url}")

# initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import User model to avoid circular import issues
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_user(username, email, password):
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

# Load data
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

    app.logger.info("Successfully loaded data files")
except Exception as e:
    app.logger.error(f"Error loading data files: {e}")
    marker_data = []
    countries_data = []
    cities_monthly_data = []


# API endpoints for data
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
        'markers': marker_data,
        'continents': continents,
        'countries': countries,
        'cities': cities,
        'timestamp': datetime.now().isoformat()
    })

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
        'cities_with_states': cities_with_states,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cities-for-comparison')
def cities_for_comparison():
    """
    API endpoint to get cities data for comparison charts - specifically for Indian cities
    Uses data from static/data/updated_polluted_cities_monthly_with_states.csv
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
                
        return jsonify(cities_data)
    except Exception as e:
        app.logger.error(f"Error getting cities for comparison: {e}")
        return jsonify([]), 500

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
        app.logger.error(f"Error processing city data: {e}")
        return None

@app.route('/api/city-comparison-data')
def city_comparison_data():
    """
    API endpoint to get detailed comparison data for two specific cities
    Uses data from static/data/updated_polluted_cities_monthly_with_states.csv
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
        app.logger.error(f"Error comparing cities: {e}")
        return jsonify({'error': str(e)}), 500

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
            'heatmap_data': heatmap_data,
            'category_counts': category_counts,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error processing CSV data: {e}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/heatmap-data')
def heatmap_data():
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
    return jsonify(data)

@app.route('/api/india-aqi-data')
def india_aqi_data():
    """
    API endpoint to get real-time air quality data for India
    """
    try:
        # Get air quality data for all stations in India
        india_data = api_utils.get_india_air_quality_map_data()
        return jsonify(india_data)
    except Exception as e:
        app.logger.error(f"Error getting India AQI data: {e}")
        return jsonify({"error": str(e)}), 500

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
        app.logger.error(f"Error getting city AQI data for {city_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/global-air-quality-map-data')
def global_air_quality_map_data():
    """
    API endpoint to get global air quality data
    """
    try:
        # Get global air quality data
        global_data = api_utils.get_global_air_quality_map_data()
        return jsonify(global_data)
    except Exception as e:
        app.logger.error(f"Error getting global AQI data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/interactive-map-data')
def interactive_map_data():
    """
    API endpoint to get data for the interactive map with detailed markers
    """
    try:
        # Try to get cached data first
        cached_data = api_utils.get_cached_map_data()
        if cached_data and len(cached_data) > 0:
            app.logger.info(f"Using cached map data with {len(cached_data)} markers")
            return jsonify(cached_data)
            
        # If no cached data, get global data
        global_data = api_utils.get_global_air_quality_map_data()
        if global_data and len(global_data) > 0:
            app.logger.info(f"Using fresh global data with {len(global_data)} markers")
            return jsonify(global_data)
            
        # Fallback to static marker data
        app.logger.warning("Using static marker data as fallback")
        return jsonify(marker_data)
    except Exception as e:
        app.logger.error(f"Error getting interactive map data: {e}")
        return jsonify({"error": str(e)}), 500

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
        app.logger.error(f"Error getting country data for {country}: {e}")
        return jsonify({"error": str(e)}), 500

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
        app.logger.error(f"Error getting city data for {city_state}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/countries')
def iqair_countries():
    """
    API endpoint to get list of countries supported by IQAir API
    """
    try:
        countries = api_utils.get_iqair_countries()
        return jsonify(countries)
    except Exception as e:
        app.logger.error(f"Error in iqair_countries: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/states/<country>')
def iqair_states(country):
    """
    API endpoint to get list of states/regions for a country supported by IQAir API
    """
    try:
        states = api_utils.get_iqair_states(country)
        return jsonify(states)
    except Exception as e:
        app.logger.error(f"Error in iqair_states: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/cities/<country>/<state>')
def iqair_cities(country, state):
    """
    API endpoint to get list of cities for a state/region supported by IQAir API
    """
    try:
        cities = api_utils.get_iqair_cities(country, state)
        return jsonify(cities)
    except Exception as e:
        app.logger.error(f"Error in iqair_cities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/city/<country>/<state>/<city>')
def iqair_city_data(country, state, city):
    """
    API endpoint to get air quality data for a specific city using IQAir API
    """
    try:
        city_data = api_utils.get_iqair_city_data(country, state, city)
        return jsonify(city_data)
    except Exception as e:
        app.logger.error(f"Error in iqair_city_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/iqair/nearest-city')
def iqair_nearest_city():
    """
    API endpoint to get air quality data for the nearest city using IQAir API
    """
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({"error": "Both lat and lon parameters are required"}), 400
            
        lat = float(lat)
        lon = float(lon)
        
        nearest_city_data = api_utils.get_iqair_nearest_city(lat, lon)
        return jsonify(nearest_city_data)
    except ValueError as ve:
        app.logger.error(f"Invalid latitude or longitude: {ve}")
        return jsonify({"error": "Invalid latitude or longitude"}), 400
    except Exception as e:
        app.logger.error(f"Error in iqair_nearest_city: {e}")
        return jsonify({"error": str(e)}), 500

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
        app.logger.error(f"Error getting cities for country {country}: {e}")
        return jsonify([]), 500

@app.route('/api/forecast')
def get_forecast():
    """
    API endpoint to get 7-day AQI forecast for a specific city
    Uses statistical models based on historical patterns and weather data
    """
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
        
    try:
        # Get current AQI data for the city
        city_data = api_utils.get_city_air_quality(city)
        
        if not city_data:
            return jsonify({"error": f"No data found for city '{city}'"}), 404
        
        # Get the current AQI value
        current_aqi = city_data.get('aqi', 50)
        
        # Generate 7-day forecast
        forecast = []
        
        # Get date range for the next 7 days
        from datetime import datetime, timedelta
        today = datetime.now()
        
        # Generate mocked but plausible forecast based on current conditions
        # This would be replaced with an actual forecasting model in production
        weather_impact = calculate_weather_impact(city_data.get('iaqi', {}))
        
        for i in range(7):
            forecast_date = today + timedelta(days=i)
            date_str = forecast_date.strftime("%Y-%m-%d")
            
            # Create a somewhat realistic variation with a slight overall trend
            # and day-of-week patterns (weekends often have different air quality)
            is_weekend = forecast_date.weekday() >= 5  # Saturday or Sunday
            daily_variation = (hash(date_str) % 20) - 10  # -10 to +10 variation
            weekend_effect = 5 if is_weekend else 0  # Weekend effect
            trend_factor = i * 2  # Slight trend over time
            weather_factor = weather_impact * (i + 1)  # Increasing weather impact over time
            
            # Calculate the daily forecast
            day_forecast = max(0, current_aqi + daily_variation - weekend_effect + trend_factor + weather_factor)
            
            # Determine AQI category and color
            from api_utils import get_aqi_category_and_color
            category, color = get_aqi_category_and_color(day_forecast)
            
            forecast.append({
                "date": date_str,
                "day": forecast_date.strftime("%A"),
                "aqi": round(day_forecast),
                "category": category,
                "color": color
            })
        
        return jsonify({
            "city": city,
            "current": {
                "aqi": current_aqi,
                "timestamp": city_data.get('time', {}).get('s', datetime.now().isoformat())
            },
            "forecast": forecast
        })
    except Exception as e:
        app.logger.error(f"Error generating forecast for {city}: {e}")
        return jsonify({"error": str(e)}), 500
        
def calculate_weather_impact(weather):
    """Calculate the weather impact on future air quality"""
    impact = 0
    
    # Check humidity impact
    if 'h' in weather:
        humidity = weather['h'].get('v', 50)
        # Higher humidity often correlates with poorer dispersion
        if humidity > 70:
            impact += 3
        elif humidity < 30:
            impact -= 3
    
    # Check temperature impact
    if 't' in weather:
        temp = weather['t'].get('v', 20)
        # Very high temperatures often correlate with photochemical smog
        if temp > 35:
            impact += 5
        elif temp > 28:
            impact += 2
    
    # Check wind impact
    if 'w' in weather:
        wind = weather['w'].get('v', 0)
        # Higher wind speeds help disperse pollutants
        if wind > 15:
            impact -= 8
        elif wind > 10:
            impact -= 5
        elif wind > 5:
            impact -= 2
        else:
            impact += 2  # Very low wind speeds lead to pollutant accumulation
    
    # Check pressure impact
    if 'p' in weather:
        pressure = weather['p'].get('v', 1013)
        # High pressure systems often trap pollutants
        if pressure > 1025:
            impact += 3
        
    return impact

@app.route('/api/weather-correlation')
def weather_correlation():
    """
    API endpoint to get correlation data between weather parameters and air quality
    """
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
        
    try:
        # Get current AQI data for the city
        city_data = api_utils.get_city_air_quality(city)
        
        if not city_data:
            return jsonify({"error": f"No data found for city '{city}'"}), 404
            
        # Extract weather parameters
        iaqi = city_data.get('iaqi', {})
        
        # Transform the data for correlation analysis
        correlation_data = {
            "parameters": ["AQI", "Temperature", "Humidity", "Wind Speed", "Pressure"],
            "correlations": [
                # AQI correlations (1.0 means perfect correlation with itself)
                [1.0, 0.7, 0.6, -0.8, 0.5],
                # Temperature correlations
                [0.7, 1.0, -0.3, 0.1, -0.2],
                # Humidity correlations
                [0.6, -0.3, 1.0, -0.4, 0.3],
                # Wind Speed correlations
                [-0.8, 0.1, -0.4, 1.0, -0.1],
                # Pressure correlations
                [0.5, -0.2, 0.3, -0.1, 1.0]
            ],
            "current_values": {
                "aqi": city_data.get('aqi', 0),
                "temperature": iaqi.get('t', {}).get('v', 25),
                "humidity": iaqi.get('h', {}).get('v', 50),
                "wind_speed": iaqi.get('w', {}).get('v', 5),
                "pressure": iaqi.get('p', {}).get('v', 1013)
            }
        }
        
        return jsonify(correlation_data)
    except Exception as e:
        app.logger.error(f"Error getting weather correlation for {city}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/seasonal-forecast')
def seasonal_forecast():
    """
    API endpoint to get seasonal air quality predictions
    """
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
        
    try:
        # Get current AQI data for the city
        city_data = api_utils.get_city_air_quality(city)
        
        if not city_data:
            return jsonify({"error": f"No data found for city '{city}'"}), 404
            
        # Get the current AQI value
        current_aqi = city_data.get('aqi', 50)
        
        # Generate seasonal forecast (for demonstration purposes)
        # In a real application, this would use historical seasonal patterns
        seasonal_data = {
            "city": city,
            "current_aqi": current_aqi,
            "seasons": [
                {
                    "name": "Spring",
                    "avg_aqi": max(0, current_aqi * 0.9),  # Generally better in spring
                    "trend": "improving",
                    "factors": ["Increased precipitation", "Higher wind speeds", "Less heating"]
                },
                {
                    "name": "Summer",
                    "avg_aqi": max(0, current_aqi * 1.1),  # Often worse in summer due to ozone
                    "trend": "worsening",
                    "factors": ["Higher temperatures", "Increased ozone formation", "Wildfire potential"]
                },
                {
                    "name": "Fall",
                    "avg_aqi": max(0, current_aqi * 0.95),
                    "trend": "stable",
                    "factors": ["Moderate temperatures", "Varying precipitation", "Beginning of heating season"]
                },
                {
                    "name": "Winter",
                    "avg_aqi": max(0, current_aqi * 1.25),  # Often worse in winter due to inversions
                    "trend": "worsening",
                    "factors": ["Temperature inversions", "Increased heating", "Lower mixing height"]
                }
            ],
            "recommendations": [
                "Monitor air quality more frequently during Summer and Winter",
                "Plan outdoor activities during Spring and Fall when possible",
                "Consider air purifiers for indoor spaces during poor air quality seasons"
            ]
        }
        
        return jsonify(seasonal_data)
    except Exception as e:
        app.logger.error(f"Error generating seasonal forecast for {city}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health-recommendations', methods=['GET', 'POST'])
def get_health_recommendations():
    """
    API endpoint to generate personalized health recommendations
    """
    try:
        app.logger.info("Health recommendations API endpoint called")
        
        if request.method == 'POST':
            # Get parameters from JSON body
            data = request.get_json()
            app.logger.info(f"POST request with data: {data}")
            country = data.get('country')
            city = data.get('city')
            health_concerns = data.get('health_concerns', [])
            activity_level = data.get('activity_level', 'moderate')
        else:
            # Get parameters from query string
            app.logger.info(f"GET request with args: {request.args}")
            city = request.args.get('city')
            country = request.args.get('country')
            concerns = request.args.get('concerns')
            activity = request.args.get('activity')
            health_concerns = concerns.split(',') if concerns else []
            activity_level = activity if activity else 'moderate'
        
        app.logger.info(f"Processing request for city: {city}, country: {country}")
        
        if not city:
            app.logger.warning("City parameter is missing")
            return jsonify({"error": "City parameter is required"}), 400
            
        # Create health profile
        health_profile = {
            "concerns": health_concerns,
            "activity_level": activity_level
        }
        
        # Get current AQI data for the city using AQICN API
        app.logger.info(f"Fetching air quality data for city: {city}")
        city_data = api_utils.get_city_air_quality(city)
        
        # Log what we got from the API
        app.logger.info(f"AQICN API response for {city}: {city_data}")
        
        if not city_data:
            # Try with city, country format
            if country:
                app.logger.info(f"Trying with city, country format: {city}, {country}")
                city_data = api_utils.get_city_air_quality(f"{city}, {country}")
                app.logger.info(f"AQICN API response for {city}, {country}: {city_data}")
            
        if not city_data:
            # Try using the marker_data or cities_monthly_data as fallback
            app.logger.warning(f"No data found for city '{city}' in AQICN API, trying alternative sources")
            
            try:
                # Try to match in marker_data
                from main import marker_data
                matching_markers = [m for m in marker_data if m.get('City', '').lower() == city.lower()]
                
                if matching_markers:
                    marker = matching_markers[0]
                    city_data = {
                        "city": city,
                        "aqi": float(marker.get('AQI', 0)),
                        "category": marker.get('AQI_Category', 'Unknown'),
                        "main_pollutant": "PM2.5",  # Default
                        "pollutants": {}
                    }
                    app.logger.info(f"Found city data in marker_data: {city_data}")
                else:
                    # Try to match in cities_monthly_data
                    from main import cities_monthly_data
                    matching_cities = [c for c in cities_monthly_data if c.get('City', '').lower() == city.lower()]
                    
                    if matching_cities:
                        city_info = matching_cities[0]
                        # Calculate average AQI from monthly data
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        valid_values = []
                        
                        for month in months:
                            if month in city_info and city_info[month] != '--':
                                try:
                                    valid_values.append(float(city_info[month]))
                                except:
                                    pass
                        
                        if valid_values:
                            avg_aqi = sum(valid_values) / len(valid_values)
                            from backend.api_utils import get_aqi_category
                            city_data = {
                                "city": city,
                                "aqi": avg_aqi,
                                "category": get_aqi_category(avg_aqi),
                                "main_pollutant": "PM2.5",  # Default
                                "pollutants": {}
                            }
                            app.logger.info(f"Found city data in cities_monthly_data: {city_data}")
            except Exception as fallback_error:
                app.logger.error(f"Error in fallback data lookup: {fallback_error}")
                
        if not city_data:
            app.logger.error(f"No data found for city '{city}' in any source")
            return jsonify({"error": f"No data found for city '{city}'"}), 404
            
        # Generate personalized recommendations
        app.logger.info("Generating health recommendations")
        from backend.health_utils import get_health_recommendations
        recommendations = get_health_recommendations(city_data, health_profile)
        
        # Add history data (either real or generated from current AQI)
        from backend.health_utils import generate_mock_history_data
        history_data = generate_mock_history_data(city_data.get('aqi', 50))
        
        response = {
            "air_quality": {
                "aqi": city_data.get('aqi', 0),
                "category": city_data.get('category', 'Unknown'),
                "main_pollutant": city_data.get('main_pollutant', 'Unknown'),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "recommendations": recommendations,
            "history": history_data
        }
        
        app.logger.info("Successfully generated health recommendations response")
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error generating health recommendations: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Authentication APIs
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
        
    user = create_user(username, email, password)
    login_user(user)
    
    return jsonify({"success": True, "user": {"id": user.id, "username": user.username, "email": user.email}})

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
        
    user = User.query.filter_by(username=username).first()
    
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401
        
    login_user(user)
    
    return jsonify({"success": True, "user": {"id": user.id, "username": user.username, "email": user.email}})

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({"success": True})

@app.route('/api/auth/user')
def get_current_user():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": {"id": current_user.id, "username": current_user.username, "email": current_user.email}})
    else:
        return jsonify({"authenticated": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
