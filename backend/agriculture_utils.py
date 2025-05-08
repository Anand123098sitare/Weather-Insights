"""
Utilities for agriculture and gardening weather forecasts and tools
"""
import os
import json
import random
import logging
import datetime
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from backend import weather_utils

logger = logging.getLogger(__name__)

# Evapotranspiration thresholds
ET_THRESHOLDS = {
    "very_low": 2.0,      # mm/day - Very low evapotranspiration
    "low": 3.5,           # mm/day - Low evapotranspiration
    "moderate": 5.0,      # mm/day - Moderate evapotranspiration
    "high": 7.0,          # mm/day - High evapotranspiration
    "very_high": 9.0      # mm/day - Very high evapotranspiration
}

# Soil type moisture characteristics
SOIL_TYPES = {
    "sandy": {
        "water_holding_capacity": 0.5,  # inches per foot
        "infiltration_rate": 2.0,       # inches per hour
        "drainage_rate": "fast",
        "description": "Sandy soils drain quickly and have low water retention"
    },
    "loamy": {
        "water_holding_capacity": 1.5,  # inches per foot
        "infiltration_rate": 0.5,       # inches per hour
        "drainage_rate": "moderate",
        "description": "Loamy soils have balanced water retention and drainage"
    },
    "clay": {
        "water_holding_capacity": 2.5,  # inches per foot
        "infiltration_rate": 0.1,       # inches per hour
        "drainage_rate": "slow",
        "description": "Clay soils retain water longer but have poor drainage"
    },
    "silty": {
        "water_holding_capacity": 2.0,  # inches per foot
        "infiltration_rate": 0.3,       # inches per hour
        "drainage_rate": "moderate-slow",
        "description": "Silty soils hold more water than sandy soils but drain faster than clay"
    }
}

# Common garden plants with their ideal conditions
COMMON_PLANTS = {
    "tomato": {
        "ideal_temp_range": (18, 29),   # Celsius
        "water_needs": "moderate",      # Water needs category
        "frost_sensitive": True,        # Is sensitive to frost
        "heat_sensitive": False,        # Not particularly sensitive to heat
        "drought_resistant": False      # Not drought resistant
    },
    "lettuce": {
        "ideal_temp_range": (10, 24),
        "water_needs": "moderate-high",
        "frost_sensitive": True,
        "heat_sensitive": True,
        "drought_resistant": False
    },
    "cucumber": {
        "ideal_temp_range": (18, 30),
        "water_needs": "high",
        "frost_sensitive": True,
        "heat_sensitive": False,
        "drought_resistant": False
    },
    "carrot": {
        "ideal_temp_range": (10, 25),
        "water_needs": "moderate",
        "frost_sensitive": False,
        "heat_sensitive": True,
        "drought_resistant": False
    },
    "pepper": {
        "ideal_temp_range": (18, 32),
        "water_needs": "moderate",
        "frost_sensitive": True,
        "heat_sensitive": False,
        "drought_resistant": False
    },
    "onion": {
        "ideal_temp_range": (13, 24),
        "water_needs": "low-moderate",
        "frost_sensitive": False,
        "heat_sensitive": False,
        "drought_resistant": False
    },
    "potato": {
        "ideal_temp_range": (15, 24),
        "water_needs": "moderate",
        "frost_sensitive": True,
        "heat_sensitive": True,
        "drought_resistant": False
    },
    "spinach": {
        "ideal_temp_range": (7, 23),
        "water_needs": "moderate",
        "frost_sensitive": False,
        "heat_sensitive": True,
        "drought_resistant": False
    }
}

def get_watering_recommendations(city: str, soil_type: str = "loamy") -> Dict[str, Any]:
    """
    Get watering recommendations based on weather forecast for a specific city and soil type
    
    Args:
        city (str): City name
        soil_type (str): Soil type (sandy, loamy, clay, silty)
        
    Returns:
        dict: Watering recommendations for the next 24 hours
    """
    try:
        # Get weather forecast
        weather_data = weather_utils.get_weather_forecast(city)
        current_weather = weather_utils.get_city_weather(city)
        
        # Current time and date
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        
        # Extract today's and tomorrow's forecasts
        today_forecast = []
        tomorrow_forecast = []
        
        if weather_data and 'list' in weather_data:
            for period in weather_data['list']:
                # Convert timestamp to datetime
                period_time = datetime.fromtimestamp(period['dt'])
                period_date = period_time.date()
                
                if period_date == today:
                    today_forecast.append(period)
                elif period_date == tomorrow:
                    tomorrow_forecast.append(period)
        
        # Use current weather if no forecast is available
        if not today_forecast and current_weather:
            today_forecast = [{
                'dt': now.timestamp(),
                'main': current_weather.get('main', {}),
                'weather': current_weather.get('weather', []),
                'clouds': current_weather.get('clouds', {}),
                'wind': current_weather.get('wind', {}),
                'pop': 0  # Probability of precipitation
            }]
        
        # Calculate daily evapotranspiration (ET) values
        today_et = calculate_evapotranspiration(today_forecast, soil_type)
        tomorrow_et = calculate_evapotranspiration(tomorrow_forecast, soil_type)
        
        # Calculate soil conditions considering recent precipitation
        recent_precipitation = get_recent_precipitation(today_forecast)
        soil_moisture = calculate_soil_moisture(soil_type, recent_precipitation, today_et)
        
        # Find upcoming precipitation
        upcoming_rain = find_upcoming_precipitation(today_forecast, tomorrow_forecast)
        
        # Determine best watering time
        best_time = determine_best_watering_time(today_forecast, tomorrow_forecast, soil_type, soil_moisture)
        
        # Generate watering plan
        watering_plan = generate_watering_plan(
            city=city,
            soil_type=soil_type,
            soil_moisture=soil_moisture,
            today_et=today_et,
            upcoming_rain=upcoming_rain,
            best_time=best_time
        )
        
        # Add weather data for the recommendation period
        today_high = max([x.get('main', {}).get('temp', 0) for x in today_forecast]) if today_forecast else 0
        today_low = min([x.get('main', {}).get('temp', 0) for x in today_forecast]) if today_forecast else 0
        
        # Get the dominant weather condition for today
        weather_conditions = [x.get('weather', [{}])[0].get('main', '') for x in today_forecast if 'weather' in x and len(x['weather']) > 0]
        dominant_condition = max(set(weather_conditions), key=weather_conditions.count) if weather_conditions else "Unknown"
        
        return {
            "city": city,
            "soil_type": soil_type,
            "soil_properties": SOIL_TYPES.get(soil_type, SOIL_TYPES["loamy"]),
            "soil_moisture": soil_moisture,
            "evapotranspiration": {
                "today": today_et,
                "tomorrow": tomorrow_et,
                "rating": get_et_rating(today_et)
            },
            "watering_recommendation": watering_plan,
            "best_watering_time": best_time,
            "upcoming_precipitation": upcoming_rain,
            "recent_precipitation": recent_precipitation,
            "weather_summary": {
                "high_temp": round(today_high, 1),
                "low_temp": round(today_low, 1),
                "condition": dominant_condition
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting watering recommendations for {city}: {e}")
        return {
            "city": city,
            "soil_type": soil_type,
            "error": str(e),
            "watering_recommendation": {
                "should_water": True,
                "message": "Unable to determine precise watering needs. As a general rule, check soil moisture by inserting your finger an inch into the soil - if it feels dry, it's time to water.",
                "water_amount": "Moderate watering recommended",
                "follow_up": "Water at sunset or early morning for best water conservation."
            },
            "timestamp": datetime.now().isoformat()
        }

def get_plant_care_recommendations(city: str, plant_type: str) -> Dict[str, Any]:
    """
    Get plant care recommendations based on weather forecast for a specific city and plant type
    
    Args:
        city (str): City name
        plant_type (str): Type of plant (tomato, lettuce, etc.)
        
    Returns:
        dict: Plant care recommendations
    """
    try:
        # Get weather forecast
        weather_data = weather_utils.get_weather_forecast(city)
        current_weather = weather_utils.get_city_weather(city)
        
        # Current time and date
        now = datetime.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)
        
        # Extract today's and tomorrow's forecasts
        today_forecast = []
        tomorrow_forecast = []
        
        if weather_data and 'list' in weather_data:
            for period in weather_data['list']:
                # Convert timestamp to datetime
                period_time = datetime.fromtimestamp(period['dt'])
                period_date = period_time.date()
                
                if period_date == today:
                    today_forecast.append(period)
                elif period_date == tomorrow:
                    tomorrow_forecast.append(period)
        
        # Use current weather if no forecast is available
        if not today_forecast and current_weather:
            today_forecast = [{
                'dt': now.timestamp(),
                'main': current_weather.get('main', {}),
                'weather': current_weather.get('weather', []),
                'clouds': current_weather.get('clouds', {}),
                'wind': current_weather.get('wind', {}),
                'pop': 0  # Probability of precipitation
            }]
            
        # Get plant information
        plant_info = COMMON_PLANTS.get(plant_type.lower(), {})
        if not plant_info:
            # If plant not found in our database, provide generic recommendations
            return {
                "city": city,
                "plant_type": plant_type,
                "status": "Plant type not found in database. Providing general recommendations.",
                "care_recommendations": [
                    "Water when the top inch of soil feels dry",
                    "Protect from extreme temperatures",
                    "Ensure proper drainage",
                    "Provide adequate sunlight"
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        # Extract temperature information from forecast
        forecast_temps = [period.get('main', {}).get('temp', 20) for period in today_forecast if 'main' in period]
        min_temp = min(forecast_temps) if forecast_temps else 0
        max_temp = max(forecast_temps) if forecast_temps else 0
        avg_temp = sum(forecast_temps) / len(forecast_temps) if forecast_temps else 0
        
        # Check for extreme conditions
        frost_risk = min_temp < 2  # Temperature below 2°C indicates frost risk
        heat_risk = max_temp > 32  # Temperature above 32°C indicates heat risk
        
        # Check for upcoming precipitation
        upcoming_rain = find_upcoming_precipitation(today_forecast, tomorrow_forecast)
        
        # Generate recommendations based on plant needs and weather conditions
        recommendations = []
        alerts = []
        
        # Temperature-based recommendations
        ideal_min, ideal_max = plant_info.get('ideal_temp_range', (10, 25))
        
        if avg_temp < ideal_min:
            if plant_info.get('frost_sensitive', False) and frost_risk:
                plant_display = plant_type.capitalize() if isinstance(plant_type, str) else "This plant"
                alerts.append({
                    "type": "frost",
                    "severity": "high",
                    "message": f"Frost risk detected! {plant_display} is sensitive to frost. Protect your plants overnight."
                })
                recommendations.append("Cover plants with frost cloth or bring them indoors if possible")
            else:
                recommendations.append(f"Current temperatures are below ideal range for {plant_type}. Consider using row covers.")
                
        elif avg_temp > ideal_max:
            if plant_info.get('heat_sensitive', False) and heat_risk:
                plant_display = plant_type.capitalize() if isinstance(plant_type, str) else "This plant"
                alerts.append({
                    "type": "heat",
                    "severity": "high",
                    "message": f"Excessive heat detected! {plant_display} is sensitive to high temperatures."
                })
                recommendations.append("Provide shade during the hottest part of the day")
                recommendations.append("Water in early morning or evening to reduce heat stress")
            else:
                recommendations.append(f"Current temperatures are above ideal range for {plant_type}. Monitor for signs of heat stress.")
        
        # Water recommendations based on precipitation forecast and plant needs
        water_needs = plant_info.get('water_needs', 'moderate')
        
        if upcoming_rain and upcoming_rain.get('expected', False):
            # Rain expected
            rain_amount = upcoming_rain.get('amount', 0)
            if water_needs == 'high' and rain_amount < 5:
                recommendations.append("Light rain expected, but may not be sufficient for this plant's needs. Supplement with additional watering if needed.")
            else:
                recommendations.append(f"Rain expected {upcoming_rain.get('timeframe', 'soon')}. Hold off on watering until after rainfall.")
        else:
            # No rain expected
            if water_needs == 'high':
                recommendations.append("No rain in forecast. Maintain regular watering schedule, checking soil moisture daily.")
            elif water_needs == 'moderate':
                recommendations.append("Water when the top inch of soil feels dry to the touch.")
            else:
                recommendations.append("Allow soil to dry between waterings. Check moisture levels by inserting finger 2 inches into soil.")
        
        # Calculate ideal watering time
        best_time = determine_best_watering_time(today_forecast, tomorrow_forecast, "loamy", 0.5)
        
        # Drone or aerial monitoring suggestions (for larger farms)
        drone_monitoring = False
        if len(today_forecast) > 0:
            weather_condition = today_forecast[0].get('weather', [{}])[0].get('main', '').lower()
            wind_speed = today_forecast[0].get('wind', {}).get('speed', 0)
            
            if ('clear' in weather_condition or 'clouds' in weather_condition) and wind_speed < 5:
                drone_monitoring = True
        
        return {
            "city": city,
            "plant_type": plant_type,
            "plant_info": plant_info,
            "weather_conditions": {
                "min_temp": round(min_temp, 1),
                "max_temp": round(max_temp, 1),
                "avg_temp": round(avg_temp, 1),
                "frost_risk": frost_risk,
                "heat_risk": heat_risk
            },
            "care_recommendations": recommendations,
            "alerts": alerts,
            "best_watering_time": best_time,
            "upcoming_precipitation": upcoming_rain,
            "suitable_for_drone_monitoring": drone_monitoring,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting plant care recommendations for {city}, {plant_type}: {e}")
        return {
            "city": city,
            "plant_type": plant_type,
            "error": str(e),
            "care_recommendations": [
                "Water early morning or evening",
                "Check soil moisture before watering",
                "Protect from extreme weather conditions"
            ],
            "timestamp": datetime.now().isoformat()
        }

def get_growing_season_forecast(city: str) -> Dict[str, Any]:
    """
    Get growing season forecast for a specific city
    
    Args:
        city (str): City name
        
    Returns:
        dict: Growing season forecast and recommendations
    """
    try:
        # Get historical weather data and forecast
        historical_data = weather_utils.get_weather_history(city)
        forecast_data = weather_utils.get_weather_forecast(city)
        
        # Current time and date
        now = datetime.now()
        current_month = now.month
        
        # Determine current season based on hemisphere
        northern_hemisphere = True  # Default to northern hemisphere
        if historical_data and 'temperature' in historical_data:
            # Use temperature pattern to determine hemisphere
            temp_pattern = historical_data['temperature']['values']
            if len(temp_pattern) >= 12:
                # Northern hemisphere: warmer in Jun-Aug (indices 5-7)
                # Southern hemisphere: warmer in Dec-Feb (indices 11, 0, 1)
                summer_north = sum(temp_pattern[5:8]) / 3
                summer_south = (temp_pattern[11] + temp_pattern[0] + temp_pattern[1]) / 3
                northern_hemisphere = summer_north > summer_south
        
        # Determine seasons based on hemisphere
        if northern_hemisphere:
            seasons = {
                "spring": [3, 4, 5],  # Mar, Apr, May
                "summer": [6, 7, 8],  # Jun, Jul, Aug
                "fall": [9, 10, 11],  # Sep, Oct, Nov
                "winter": [12, 1, 2]  # Dec, Jan, Feb
            }
        else:
            seasons = {
                "spring": [9, 10, 11],  # Sep, Oct, Nov
                "summer": [12, 1, 2],   # Dec, Jan, Feb
                "fall": [3, 4, 5],      # Mar, Apr, May
                "winter": [6, 7, 8]     # Jun, Jul, Aug
            }
            
        # Determine current season
        current_season = next((season for season, months in seasons.items() if current_month in months), "unknown")
        
        # Get next season
        season_order = ["winter", "spring", "summer", "fall"]
        current_season_index = season_order.index(current_season) if current_season in season_order else 0
        next_season = season_order[(current_season_index + 1) % 4]
        
        # Generate planting recommendations based on season
        planting_recommendations = generate_planting_recommendations(current_season, next_season, northern_hemisphere)
        
        # Extract temperature and precipitation forecast for next 5 days
        five_day_forecast = []
        if forecast_data and 'list' in forecast_data:
            # Group forecast by day
            forecast_by_day = {}
            for period in forecast_data['list']:
                day = datetime.fromtimestamp(period['dt']).date()
                if day not in forecast_by_day:
                    forecast_by_day[day] = []
                forecast_by_day[day].append(period)
            
            # Process the first 5 days
            days_processed = 0
            for day, periods in sorted(forecast_by_day.items()):
                if days_processed >= 5:
                    break
                    
                # Calculate min/max temperature and precipitation probability
                temps = [p.get('main', {}).get('temp', 0) for p in periods if 'main' in p]
                min_temp = min(temps) if temps else 0
                max_temp = max(temps) if temps else 0
                
                # Get average precipitation probability
                precip_probs = [p.get('pop', 0) * 100 for p in periods if 'pop' in p]  # Convert to percentage
                avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else 0
                
                # Get weather condition
                weather_conditions = [p.get('weather', [{}])[0].get('main', '') for p in periods if 'weather' in p and len(p['weather']) > 0]
                dominant_condition = max(set(weather_conditions), key=weather_conditions.count) if weather_conditions else "Unknown"
                
                five_day_forecast.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "day_name": day.strftime("%A"),
                    "min_temp": round(min_temp, 1),
                    "max_temp": round(max_temp, 1),
                    "precipitation_probability": round(avg_precip_prob, 1),
                    "condition": dominant_condition
                })
                
                days_processed += 1
        
        # Extract temperature extremes
        if historical_data and 'temperature' in historical_data:
            temperature_data = historical_data['temperature']
            monthly_temps = temperature_data.get('values', [20] * 12)  # Default to 20°C if no data
            
            # Calculate seasonal averages
            seasonal_temps = {}
            for season, months in seasons.items():
                # Convert 1-based months to 0-based indices
                indices = [(m - 1) % 12 for m in months]
                seasonal_temps[season] = sum(monthly_temps[i] for i in indices if i < len(monthly_temps)) / len(indices)
        else:
            seasonal_temps = {
                "spring": 15,
                "summer": 25,
                "fall": 15,
                "winter": 5
            }
        
        return {
            "city": city,
            "hemisphere": "Northern" if northern_hemisphere else "Southern",
            "current_season": current_season,
            "next_season": next_season,
            "seasonal_temperatures": {s: round(t, 1) for s, t in seasonal_temps.items()},
            "five_day_forecast": five_day_forecast,
            "planting_recommendations": planting_recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting growing season forecast for {city}: {e}")
        return {
            "city": city,
            "error": str(e),
            "planting_recommendations": [
                "Check local gardening resources for specific planting dates in your region",
                "Consider starting seeds indoors for transplanting later",
                "Monitor soil temperature before planting heat-loving crops"
            ],
            "timestamp": datetime.now().isoformat()
        }

def get_soil_moisture_forecast(city: str, soil_type: str = "loamy") -> Dict[str, Any]:
    """
    Get soil moisture forecast for a specific city and soil type
    
    Args:
        city (str): City name
        soil_type (str): Soil type (sandy, loamy, clay, silty)
        
    Returns:
        dict: Soil moisture forecast for the next 5 days
    """
    try:
        # Get weather forecast
        weather_data = weather_utils.get_weather_forecast(city)
        
        # Current time and date
        now = datetime.now()
        
        # Extract forecasts and group by day
        daily_forecasts = {}
        
        if weather_data and 'list' in weather_data:
            for period in weather_data['list']:
                # Convert timestamp to datetime
                period_time = datetime.fromtimestamp(period['dt'])
                period_date = period_time.date()
                
                if period_date not in daily_forecasts:
                    daily_forecasts[period_date] = []
                    
                daily_forecasts[period_date].append(period)
        
        # Process each day's forecast
        moisture_forecast = []
        current_moisture = 0.7  # Starting soil moisture level (0-1 scale, 0.7 = 70%)
        
        # Get soil properties
        soil_properties = SOIL_TYPES.get(soil_type, SOIL_TYPES["loamy"])
        water_holding_capacity = soil_properties["water_holding_capacity"]
        infiltration_rate = soil_properties["infiltration_rate"]
        
        for day, forecast in sorted(daily_forecasts.items()):
            # Calculate daily ET
            daily_et = calculate_evapotranspiration(forecast, soil_type)
            
            # Calculate precipitation
            precip_probs = [p.get('pop', 0) for p in forecast if 'pop' in p]
            avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else 0
            
            # Estimate precipitation amount based on probability
            # This is a simplified model; real precipitation would come from the API
            estimated_precip = 0
            if avg_precip_prob > 0.7:
                estimated_precip = random.uniform(10, 25)  # Heavy rain
            elif avg_precip_prob > 0.4:
                estimated_precip = random.uniform(2, 10)   # Moderate rain
            elif avg_precip_prob > 0.2:
                estimated_precip = random.uniform(0.1, 2)  # Light rain
                
            # Convert mm to inches for calculation
            estimated_precip_inches = estimated_precip / 25.4
            daily_et_inches = daily_et / 25.4
            
            # Calculate moisture gain from precipitation (limited by infiltration rate)
            moisture_gain = min(estimated_precip_inches, infiltration_rate) / water_holding_capacity
            
            # Calculate moisture loss from ET
            moisture_loss = daily_et_inches / water_holding_capacity
            
            # Update current moisture level
            current_moisture = min(1.0, max(0.0, current_moisture + moisture_gain - moisture_loss))
            
            # Determine moisture status
            if current_moisture < 0.3:
                moisture_status = "Dry"
                moisture_class = "danger"
                watering_needed = "High priority"
            elif current_moisture < 0.5:
                moisture_status = "Moderate"
                moisture_class = "warning"
                watering_needed = "Consider watering"
            elif current_moisture < 0.7:
                moisture_status = "Adequate"
                moisture_class = "info"
                watering_needed = "Monitor conditions"
            else:
                moisture_status = "Good"
                moisture_class = "success"
                watering_needed = "No watering needed"
            
            # Get weather condition
            weather_conditions = [p.get('weather', [{}])[0].get('main', '') for p in forecast if 'weather' in p and len(p['weather']) > 0]
            dominant_condition = max(set(weather_conditions), key=weather_conditions.count) if weather_conditions else "Unknown"
            
            # Format date
            formatted_date = day.strftime("%Y-%m-%d")
            day_name = day.strftime("%A")
            
            moisture_forecast.append({
                "date": formatted_date,
                "day_name": day_name,
                "soil_moisture": round(current_moisture * 100, 1),  # Convert to percentage
                "moisture_status": moisture_status,
                "moisture_class": moisture_class,
                "evapotranspiration": round(daily_et, 2),
                "precipitation_probability": round(avg_precip_prob * 100, 1),
                "estimated_precipitation": round(estimated_precip, 1),
                "watering_recommendation": watering_needed,
                "weather_condition": dominant_condition
            })
            
            # Limit to 5 days
            if len(moisture_forecast) >= 5:
                break
        
        return {
            "city": city,
            "soil_type": soil_type,
            "soil_properties": soil_properties,
            "moisture_forecast": moisture_forecast,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting soil moisture forecast for {city}: {e}")
        return {
            "city": city,
            "soil_type": soil_type,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_pest_risk_forecast(city: str) -> Dict[str, Any]:
    """
    Get pest and disease risk forecast based on weather conditions
    
    Args:
        city (str): City name
        
    Returns:
        dict: Pest and disease risk assessments for the coming days
    """
    try:
        # Get weather forecast
        weather_data = weather_utils.get_weather_forecast(city)
        
        # Common garden pests and their favorable conditions
        pests = {
            "aphids": {
                "favorable_temp": (20, 30),  # Celsius
                "favorable_humidity": (60, 90),  # Percentage
                "description": "Small sap-sucking insects that can quickly multiply in warm conditions",
                "control_methods": ["Introduce beneficial insects", "Neem oil spray", "Insecticidal soap"]
            },
            "slugs_snails": {
                "favorable_temp": (5, 25),
                "favorable_humidity": (70, 100),
                "description": "Mollusks that feed on plant leaves and are most active in moist conditions",
                "control_methods": ["Diatomaceous earth barriers", "Beer traps", "Copper tape barriers"]
            },
            "spider_mites": {
                "favorable_temp": (27, 38),
                "favorable_humidity": (20, 40),
                "description": "Tiny pests that thrive in hot, dry conditions and cause stippling on leaves",
                "control_methods": ["Increase humidity", "Neem oil", "Predatory mites"]
            },
            "powdery_mildew": {
                "favorable_temp": (15, 28),
                "favorable_humidity": (50, 90),
                "description": "Fungal disease causing white powdery spots on leaves in warm, humid conditions",
                "control_methods": ["Improve air circulation", "Baking soda spray", "Fungicides"]
            },
            "late_blight": {
                "favorable_temp": (10, 24),
                "favorable_humidity": (75, 100),
                "description": "Fungal disease affecting tomatoes and potatoes, thrives in cool, wet conditions",
                "control_methods": ["Copper fungicides", "Proper spacing", "Avoid overhead watering"]
            }
        }
        
        # Extract 5-day forecast
        daily_forecasts = {}
        
        if weather_data and 'list' in weather_data:
            for period in weather_data['list']:
                # Convert timestamp to datetime
                period_time = datetime.fromtimestamp(period['dt'])
                period_date = period_time.date()
                
                if period_date not in daily_forecasts:
                    daily_forecasts[period_date] = []
                    
                daily_forecasts[period_date].append(period)
        
        # Process pest risks for each day
        risk_forecast = []
        
        for day, forecast in sorted(daily_forecasts.items()):
            # Calculate average temperature and humidity
            temps = [p.get('main', {}).get('temp', 20) for p in forecast if 'main' in p]
            humidities = [p.get('main', {}).get('humidity', 50) for p in forecast if 'main' in p]
            
            avg_temp = sum(temps) / len(temps) if temps else 20
            avg_humidity = sum(humidities) / len(humidities) if humidities else 50
            
            # Get precipitation probability
            precip_probs = [p.get('pop', 0) for p in forecast if 'pop' in p]
            avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else 0
            
            # Determine risk level for each pest
            pest_risks = {}
            for pest, conditions in pests.items():
                # Check if conditions are favorable
                temp_range = conditions["favorable_temp"]
                humidity_range = conditions["favorable_humidity"]
                
                temp_favorable = temp_range[0] <= avg_temp <= temp_range[1]
                humidity_favorable = humidity_range[0] <= avg_humidity <= humidity_range[1]
                
                # Special case for slugs and late blight - higher risk with precipitation
                precipitation_factor = 0
                if pest in ["slugs_snails", "late_blight"] and avg_precip_prob > 0.3:
                    precipitation_factor = avg_precip_prob * 2
                
                # Calculate risk factor (0-10 scale)
                risk_factor = 0
                if temp_favorable and humidity_favorable:
                    risk_factor = 7 + precipitation_factor
                elif temp_favorable or humidity_favorable:
                    risk_factor = 3 + precipitation_factor
                
                # Cap at 10
                risk_factor = min(10, risk_factor)
                
                # Determine risk level
                if risk_factor >= 7:
                    risk_level = "high"
                    risk_class = "danger"
                elif risk_factor >= 4:
                    risk_level = "moderate"
                    risk_class = "warning"
                else:
                    risk_level = "low"
                    risk_class = "success"
                
                pest_risks[pest] = {
                    "risk_factor": round(risk_factor, 1),
                    "risk_level": risk_level,
                    "risk_class": risk_class,
                    "description": conditions["description"],
                    "control_methods": conditions["control_methods"]
                }
            
            # Get weather condition
            weather_conditions = [p.get('weather', [{}])[0].get('main', '') for p in forecast if 'weather' in p and len(p['weather']) > 0]
            dominant_condition = max(set(weather_conditions), key=weather_conditions.count) if weather_conditions else "Unknown"
            
            # Format date
            formatted_date = day.strftime("%Y-%m-%d")
            day_name = day.strftime("%A")
            
            # Find highest risk pest for summary
            highest_risk_pest = max(pest_risks.items(), key=lambda x: x[1]["risk_factor"]) if pest_risks else None
            summary = ""
            if highest_risk_pest and highest_risk_pest[1]["risk_factor"] >= 7:
                pest_name = highest_risk_pest[0].replace("_", " ").title()
                summary = f"High risk of {pest_name}. Consider preventative measures."
            elif highest_risk_pest and highest_risk_pest[1]["risk_factor"] >= 4:
                pest_name = highest_risk_pest[0].replace("_", " ").title()
                summary = f"Moderate risk of {pest_name}. Monitor plants closely."
            else:
                summary = "Low pest risk. Continue routine monitoring."
            
            risk_forecast.append({
                "date": formatted_date,
                "day_name": day_name,
                "weather_summary": {
                    "temperature": round(avg_temp, 1),
                    "humidity": round(avg_humidity, 1),
                    "precipitation_probability": round(avg_precip_prob * 100, 1),
                    "condition": dominant_condition
                },
                "pest_risks": pest_risks,
                "risk_summary": summary
            })
            
            # Limit to 5 days
            if len(risk_forecast) >= 5:
                break
        
        return {
            "city": city,
            "risk_forecast": risk_forecast,
            "pests_info": pests,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting pest risk forecast for {city}: {e}")
        return {
            "city": city,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Helper functions

def calculate_evapotranspiration(forecast_periods: List[Dict[str, Any]], soil_type: str) -> float:
    """
    Calculate estimated evapotranspiration based on forecast data
    Uses a simplified version of the Penman-Monteith equation
    
    Args:
        forecast_periods (list): List of forecast periods for a day
        soil_type (str): Soil type for adjustment
        
    Returns:
        float: Estimated evapotranspiration in mm/day
    """
    if not forecast_periods:
        return 3.0  # Default moderate value if no data
    
    # Extract relevant data from forecast
    temps = []
    humidities = []
    wind_speeds = []
    cloud_covers = []
    
    for period in forecast_periods:
        if 'main' in period and 'temp' in period['main']:
            temps.append(period['main']['temp'])
        if 'main' in period and 'humidity' in period['main']:
            humidities.append(period['main']['humidity'])
        if 'wind' in period and 'speed' in period['wind']:
            wind_speeds.append(period['wind']['speed'])
        if 'clouds' in period and 'all' in period['clouds']:
            cloud_covers.append(period['clouds']['all'])
    
    # Calculate averages
    avg_temp = sum(temps) / len(temps) if temps else 20
    avg_humidity = sum(humidities) / len(humidities) if humidities else 50
    avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 2
    avg_cloud = sum(cloud_covers) / len(cloud_covers) if cloud_covers else 50
    
    # Adjust temperature factor (higher temp = higher ET)
    temp_factor = 0.05 * avg_temp
    
    # Adjust humidity factor (lower humidity = higher ET)
    humidity_factor = 5 - (0.05 * avg_humidity)
    
    # Adjust wind factor (higher wind = higher ET)
    wind_factor = 0.2 * avg_wind
    
    # Adjust cloud factor (lower cloud cover = higher ET)
    cloud_factor = 2 - (0.02 * avg_cloud)
    
    # Soil adjustment (sandy soils dry faster)
    soil_factor = 1.0
    if soil_type == "sandy":
        soil_factor = 1.2
    elif soil_type == "clay":
        soil_factor = 0.8
    
    # Calculate ET (mm/day)
    et = (temp_factor + humidity_factor + wind_factor + cloud_factor) * soil_factor
    
    # Ensure reasonable range
    et = max(1.0, min(et, 15.0))
    
    return et

def get_et_rating(et_value: float) -> str:
    """Get evapotranspiration rating based on value"""
    if et_value < ET_THRESHOLDS["very_low"]:
        return "very_low"
    elif et_value < ET_THRESHOLDS["low"]:
        return "low"
    elif et_value < ET_THRESHOLDS["moderate"]:
        return "moderate"
    elif et_value < ET_THRESHOLDS["high"]:
        return "high"
    else:
        return "very_high"

def get_recent_precipitation(forecast_periods: List[Dict[str, Any]]) -> float:
    """
    Calculate recent precipitation from forecast data
    
    Args:
        forecast_periods (list): List of forecast periods
        
    Returns:
        float: Recent precipitation in mm
    """
    precipitation = 0
    
    for period in forecast_periods:
        # Check for 'rain' field which contains precipitation data
        if 'rain' in period and '3h' in period['rain']:
            precipitation += period['rain']['3h']
            
    return precipitation

def determine_best_watering_time(today_forecast: List[Dict[str, Any]], tomorrow_forecast: List[Dict[str, Any]], 
                                soil_type: str, soil_moisture: float) -> Dict[str, Any]:
    """
    Determine the best time for watering based on forecast and conditions
    
    Args:
        today_forecast (list): Today's forecast periods
        tomorrow_forecast (list): Tomorrow's forecast periods
        soil_type (str): Soil type
        soil_moisture (float): Current soil moisture level (0-1)
        
    Returns:
        dict: Best watering time recommendation
    """
    # If soil is already very moist, delay watering
    if soil_moisture > 0.8:
        return {
            "should_water": False,
            "time": None,
            "day": "tomorrow",
            "reasons": ["Soil is already adequately moist", "Delaying watering to prevent overwatering"]
        }
    
    # Check for upcoming rain in the next 24 hours
    upcoming_rain = find_upcoming_precipitation(today_forecast, tomorrow_forecast)
    if upcoming_rain and upcoming_rain.get('expected', False) and upcoming_rain.get('amount', 0) > 5:
        return {
            "should_water": False,
            "time": None,
            "day": "after rain",
            "reasons": [f"Significant rain ({upcoming_rain.get('amount', 0)} mm) expected {upcoming_rain.get('timeframe', 'soon')}", 
                       "Natural rainfall is better for plants than irrigation"]
        }
    
    # Get current time
    now = datetime.now()
    current_hour = now.hour
    
    # Best watering times in priority order - early morning or evening
    preferred_times = [
        {"hour": 19, "period": "evening"},  # 7 PM
        {"hour": 20, "period": "evening"},  # 8 PM
        {"hour": 6, "period": "morning"},   # 6 AM
        {"hour": 7, "period": "morning"}    # 7 AM
    ]
    
    # Find the next available preferred time
    for time_slot in preferred_times:
        hour = time_slot["hour"]
        period = time_slot["period"]
        
        # If we've passed this time today, check tomorrow unless it's evening
        if hour <= current_hour and period != "evening":
            continue
            
        # Check if this time has good conditions (no rain, not too windy)
        good_conditions = True
        
        # Find the forecast period closest to this hour
        target_forecast = today_forecast if hour > current_hour else tomorrow_forecast
        
        for period in target_forecast:
            period_time = datetime.fromtimestamp(period['dt'])
            if abs(period_time.hour - hour) <= 1:  # Within 1 hour of target
                # Check for rain
                if 'rain' in period:
                    good_conditions = False
                    break
                    
                # Check for wind (avoid watering when it's too windy)
                if 'wind' in period and 'speed' in period['wind'] and period['wind']['speed'] > 5:
                    good_conditions = False
                    break
        
        if good_conditions:
            # Convert 24h to 12h format
            hour_12 = hour % 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            ampm = "AM" if hour < 12 else "PM"
            
            day = "today" if hour > current_hour else "tomorrow"
            
            period_display = period.capitalize() if isinstance(period, str) else "Evening"
            reasons = [
                f"{period_display} watering reduces evaporation",
                "Plants have time to dry before nightfall, reducing disease risk"
            ]
            
            if soil_type == "sandy":
                reasons.append("Sandy soil benefits from evening watering to retain moisture longer")
            elif soil_type == "clay":
                reasons.append("Clay soil benefits from morning watering to prevent waterlogging overnight")
            
            return {
                "should_water": True,
                "time": f"{hour_12} {ampm}",
                "hour_24": hour, 
                "day": day,
                "reasons": reasons
            }
    
    # If no good time found, recommend evening watering as default
    return {
        "should_water": True,
        "time": "7 PM",
        "hour_24": 19,
        "day": "today" if current_hour < 19 else "tomorrow",
        "reasons": ["Evening watering reduces evaporation", "Allows soil to absorb moisture overnight"]
    }

def find_upcoming_precipitation(today_forecast: List[Dict[str, Any]], tomorrow_forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find upcoming precipitation events in the forecast
    
    Args:
        today_forecast (list): Today's forecast periods
        tomorrow_forecast (list): Tomorrow's forecast periods
        
    Returns:
        dict: Upcoming precipitation details
    """
    # Check today's forecast first
    for period in today_forecast:
        period_time = datetime.fromtimestamp(period['dt'])
        
        # Check for rain probability
        pop = period.get('pop', 0)  # Probability of precipitation
        
        # Check for rain amount
        rain_amount = 0
        if 'rain' in period and '3h' in period['rain']:
            rain_amount = period['rain']['3h']
        
        # If significant rain expected
        if pop > 0.4 or rain_amount > 0:
            return {
                "expected": True,
                "probability": pop * 100,  # Convert to percentage
                "amount": rain_amount,
                "time": period_time.strftime('%H:%M'),
                "timeframe": "later today",
                "timestamp": period['dt']
            }
    
    # Check tomorrow's forecast
    for period in tomorrow_forecast:
        period_time = datetime.fromtimestamp(period['dt'])
        
        # Check for rain probability
        pop = period.get('pop', 0)
        
        # Check for rain amount
        rain_amount = 0
        if 'rain' in period and '3h' in period['rain']:
            rain_amount = period['rain']['3h']
        
        # If significant rain expected
        if pop > 0.4 or rain_amount > 0:
            return {
                "expected": True,
                "probability": pop * 100,
                "amount": rain_amount,
                "time": period_time.strftime('%H:%M'),
                "timeframe": "tomorrow",
                "timestamp": period['dt']
            }
    
    # No significant precipitation expected
    return {
        "expected": False,
        "timeframe": "next 48 hours"
    }

def calculate_soil_moisture(soil_type: str, recent_precipitation: float, evapotranspiration: float) -> float:
    """
    Calculate estimated soil moisture based on recent precipitation and evapotranspiration
    
    Args:
        soil_type (str): Soil type
        recent_precipitation (float): Recent precipitation in mm
        evapotranspiration (float): Daily evapotranspiration in mm
        
    Returns:
        float: Estimated soil moisture level (0-1 scale)
    """
    # Get soil properties
    soil_properties = SOIL_TYPES.get(soil_type, SOIL_TYPES["loamy"])
    
    # Base moisture level (0-1 scale)
    base_moisture = 0.5  # Start with medium moisture
    
    # Convert precipitation to moisture gain
    # This is a simplified model; real soil moisture is more complex
    precip_factor = 0.05  # Each mm of rain increases moisture by 5%
    moisture_from_precip = min(0.5, recent_precipitation * precip_factor)  # Cap at 50%
    
    # Convert ET to moisture loss
    et_factor = 0.04  # Each mm of ET decreases moisture by 4%
    moisture_loss = min(0.5, evapotranspiration * et_factor)  # Cap at 50%
    
    # Adjust for soil type
    soil_factor = 1.0
    if soil_type == "sandy":
        soil_factor = 0.8  # Sandy soil holds less water
    elif soil_type == "clay":
        soil_factor = 1.2  # Clay soil holds more water
    
    # Calculate soil moisture
    soil_moisture = (base_moisture + moisture_from_precip - moisture_loss) * soil_factor
    
    # Ensure value is between 0 and 1
    soil_moisture = max(0.0, min(1.0, soil_moisture))
    
    return soil_moisture

def generate_watering_plan(city: str, soil_type: str, soil_moisture: float, today_et: float, 
                           upcoming_rain: Dict[str, Any], best_time: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a watering plan based on conditions
    
    Args:
        city (str): City name
        soil_type (str): Soil type
        soil_moisture (float): Current soil moisture (0-1)
        today_et (float): Today's evapotranspiration
        upcoming_rain (dict): Upcoming rain forecast
        best_time (dict): Best watering time recommendation
        
    Returns:
        dict: Watering plan recommendation
    """
    # Check if watering is needed
    should_water = True
    water_amount = "Moderate watering"  # Default value
    
    # Don't water if soil is already moist
    if soil_moisture > 0.7:
        should_water = False
        message = "Soil moisture is adequate. No need to water at this time."
        details = ["Allow soil to dry slightly before watering again", 
                  "Check soil moisture by inserting finger 1-2 inches into soil"]
    
    # Don't water if significant rain is expected soon
    elif upcoming_rain.get('expected', False) and upcoming_rain.get('amount', 0) > 5:
        should_water = False
        message = f"Rain expected {upcoming_rain.get('timeframe', 'soon')}. Hold off on watering."
        details = [f"Expected rainfall: {upcoming_rain.get('amount', 0)} mm", 
                  "Natural rain is better for plants than irrigation water"]
    
    # Otherwise, generate watering recommendation
    else:
        # Determine watering amount based on soil moisture and ET
        if soil_moisture < 0.3:
            water_amount = "Heavy watering"
            water_amount_details = "Water deeply to saturate the root zone (about 1 inch of water)"
        elif soil_moisture < 0.5:
            water_amount = "Moderate watering"
            water_amount_details = "Apply about 1/2 to 3/4 inch of water"
        else:
            water_amount = "Light watering"
            water_amount_details = "Apply about 1/4 to 1/2 inch of water"
            
        # Adjust for soil type
        if soil_type == "sandy":
            water_frequency = "More frequent, lighter waterings are better for sandy soil"
        elif soil_type == "clay":
            water_frequency = "Less frequent, deeper waterings are better for clay soil"
        else:
            water_frequency = "Balanced watering approach works well for loamy soil"
        
        # Adjust for evapotranspiration
        et_rating = get_et_rating(today_et)
        if et_rating in ["high", "very_high"]:
            et_note = f"High evapotranspiration ({today_et:.1f} mm/day) means plants lose moisture quickly"
        else:
            et_note = f"Moderate evapotranspiration ({today_et:.1f} mm/day) means moisture loss is typical"
        
        message = f"Water your garden at {best_time.get('time', '7 PM')} {best_time.get('day', 'today')}."
        details = [
            water_amount_details,
            water_frequency,
            et_note
        ]
    
    return {
        "should_water": should_water,
        "message": message,
        "details": details,
        "best_time": best_time,
        "water_amount": water_amount if should_water else "No watering needed"
    }

def generate_planting_recommendations(current_season: str, next_season: str, northern_hemisphere: bool) -> Dict[str, Any]:
    """
    Generate planting recommendations based on season and hemisphere
    
    Args:
        current_season (str): Current season
        next_season (str): Next season
        northern_hemisphere (bool): Whether in northern hemisphere
        
    Returns:
        dict: Planting recommendations
    """
    # Season-specific recommendations
    spring_plants = ["Tomatoes", "Peppers", "Cucumbers", "Squash", "Beans", "Corn"]
    summer_plants = ["Basil", "Okra", "Sweet Potatoes", "Eggplant", "Melons", "Heat-resistant Lettuce"]
    fall_plants = ["Spinach", "Lettuce", "Kale", "Radishes", "Carrots", "Broccoli"]
    winter_plants = ["Garlic", "Winter Onions", "Cover Crops", "Broad Beans", "Winter Lettuce"]
    
    recommendations = {
        "current_season": {
            "season": current_season,
            "plants_to_maintain": [],
            "harvest_soon": [],
            "care_tips": []
        },
        "next_season": {
            "season": next_season,
            "plants_to_start": [],
            "preparation_tips": []
        }
    }
    
    # Current season recommendations
    if current_season == "spring":
        recommendations["current_season"]["plants_to_maintain"] = spring_plants
        recommendations["current_season"]["harvest_soon"] = ["Early Lettuce", "Radishes", "Spring Onions"]
        recommendations["current_season"]["care_tips"] = [
            "Monitor for late frosts and protect tender seedlings",
            "Begin regular fertilization schedule",
            "Set up supports for climbing plants",
            "Thin seedlings to proper spacing"
        ]
    elif current_season == "summer":
        recommendations["current_season"]["plants_to_maintain"] = summer_plants
        recommendations["current_season"]["harvest_soon"] = ["Tomatoes", "Cucumbers", "Zucchini", "Summer Squash"]
        recommendations["current_season"]["care_tips"] = [
            "Water deeply and consistently in morning or evening",
            "Mulch to conserve moisture",
            "Provide shade for heat-sensitive crops",
            "Monitor for pests that thrive in warm weather"
        ]
    elif current_season == "fall":
        recommendations["current_season"]["plants_to_maintain"] = fall_plants
        recommendations["current_season"]["harvest_soon"] = ["Late Tomatoes", "Peppers", "Root Vegetables"]
        recommendations["current_season"]["care_tips"] = [
            "Protect cold-sensitive crops from early frosts",
            "Add compost to harvested areas",
            "Clean up garden debris to prevent disease carryover",
            "Reduce watering as temperatures cool"
        ]
    elif current_season == "winter":
        recommendations["current_season"]["plants_to_maintain"] = winter_plants
        recommendations["current_season"]["harvest_soon"] = ["Winter Greens", "Brussels Sprouts", "Stored Root Vegetables"]
        recommendations["current_season"]["care_tips"] = [
            "Protect overwintering crops with row covers or cold frames",
            "Monitor soil moisture in protected areas",
            "Plan next season's garden",
            "Order seeds for next growing season"
        ]
    
    # Next season recommendations
    if next_season == "spring":
        recommendations["next_season"]["plants_to_start"] = spring_plants
        recommendations["next_season"]["preparation_tips"] = [
            "Start seeds indoors for warm-season crops",
            "Prepare soil with compost and amendments",
            "Clean and sharpen gardening tools",
            "Set up irrigation systems before planting"
        ]
    elif next_season == "summer":
        recommendations["next_season"]["plants_to_start"] = summer_plants
        recommendations["next_season"]["preparation_tips"] = [
            "Install shade cloth for heat-sensitive plants",
            "Set up consistent watering system",
            "Mulch extensively to conserve moisture",
            "Plan succession plantings for continual harvest"
        ]
    elif next_season == "fall":
        recommendations["next_season"]["plants_to_start"] = fall_plants
        recommendations["next_season"]["preparation_tips"] = [
            "Start seeds for fall crops in a cool, shaded area",
            "Prepare areas where summer crops will be removed",
            "Add compost to replenish soil nutrients",
            "Have frost protection ready for late season"
        ]
    elif next_season == "winter":
        recommendations["next_season"]["plants_to_start"] = winter_plants
        recommendations["next_season"]["preparation_tips"] = [
            "Install cold frames or hoop houses",
            "Add heavy mulch to protect perennial crops",
            "Plant cover crops in empty beds",
            "Set up protection for winter harvests"
        ]
    
    # Adjust for hemisphere differences
    if not northern_hemisphere:
        # Swap some plants for southern hemisphere appropriate ones
        # This is a simplified adjustment; real recommendations would be more nuanced
        spring_specific = ["Artichokes", "Passion Fruit", "Subtropical Berries"]
        if current_season == "spring":
            recommendations["current_season"]["plants_to_maintain"].extend(spring_specific)
        if next_season == "spring":
            recommendations["next_season"]["plants_to_start"].extend(spring_specific)
    
    return recommendations