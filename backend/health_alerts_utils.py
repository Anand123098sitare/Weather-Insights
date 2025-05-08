"""
Utilities for health alerts related to weather and air quality
"""
import os
import json
import random
import logging
import datetime
from typing import Dict, List, Optional, Union, Any

from backend import api_utils, health_utils, weather_utils

logger = logging.getLogger(__name__)

def get_pollen_count(city: str, date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """
    Get pollen count for a specific city and date
    
    Args:
        city (str): City name
        date (datetime, optional): Date for pollen count. Defaults to current date.
        
    Returns:
        dict: Pollen count data
    """
    try:
        if date is None:
            date = datetime.datetime.now()
            
        # Get weather and air quality data to derive pollen conditions
        weather_data = weather_utils.get_city_weather(city)
        aqi_data = api_utils.get_city_air_quality(city)
        
        # Base pollen factors on weather conditions
        temperature = weather_data.get('main', {}).get('temp', 20)
        humidity = weather_data.get('main', {}).get('humidity', 50)
        wind_speed = weather_data.get('wind', {}).get('speed', 5)
        weather_condition = weather_data.get('weather', [{}])[0].get('main', '').lower()
        
        # Calculate base pollen level based on weather
        base_pollen_level = 3  # Default moderate level

        # Adjust for temperature (higher temps generally increase pollen)
        if temperature > 30:
            base_pollen_level += 2
        elif temperature > 25:
            base_pollen_level += 1
        elif temperature < 10:
            base_pollen_level -= 1
            
        # Adjust for humidity (higher humidity can reduce some pollen)
        if humidity > 80:
            base_pollen_level -= 1
        elif humidity < 30:
            base_pollen_level += 1
            
        # Adjust for wind (higher wind spreads pollen)
        if wind_speed > 20:
            base_pollen_level += 2
        elif wind_speed > 10:
            base_pollen_level += 1
            
        # Adjust for weather conditions
        if 'rain' in weather_condition or 'drizzle' in weather_condition:
            base_pollen_level -= 2  # Rain washes pollen away
        elif 'snow' in weather_condition:
            base_pollen_level -= 3  # Snow suppresses pollen
        elif 'clear' in weather_condition:
            base_pollen_level += 1  # Clear days can have higher pollen
            
        # Ensure pollen level is within range 1-10
        overall_pollen_level = max(1, min(10, base_pollen_level))
        
        # Determine category based on level
        if overall_pollen_level <= 3:
            category = "Low"
            description = "Most people won't be affected."
            alert_type = "success"
        elif overall_pollen_level <= 6:
            category = "Moderate"
            description = "Some individuals may experience symptoms."
            alert_type = "info"
        elif overall_pollen_level <= 8:
            category = "High"
            description = "Many people will experience symptoms."
            alert_type = "warning"
        else:
            category = "Very High"
            description = "Most people with allergies will experience symptoms."
            alert_type = "danger"
            
        # Different pollen types based on month
        month = date.month
        active_pollen_types = []
        
        # Spring (March-May): Tree pollen dominant
        if 3 <= month <= 5:
            active_pollen_types = ["tree", "grass", "weed"]
            # Tree pollen highest in spring
            pollen_levels = {
                "tree": min(10, overall_pollen_level + random.randint(0, 2)),
                "grass": max(1, overall_pollen_level - random.randint(1, 3)),
                "weed": max(1, overall_pollen_level - random.randint(2, 4))
            }
        # Summer (June-August): Grass pollen dominant
        elif 6 <= month <= 8:
            active_pollen_types = ["grass", "weed", "tree"]
            # Grass pollen highest in summer
            pollen_levels = {
                "grass": min(10, overall_pollen_level + random.randint(0, 2)),
                "weed": min(10, overall_pollen_level),
                "tree": max(1, overall_pollen_level - random.randint(2, 4))
            }
        # Fall (September-November): Weed pollen dominant
        elif 9 <= month <= 11:
            active_pollen_types = ["weed", "mold", "grass"]
            # Weed pollen highest in fall
            pollen_levels = {
                "weed": min(10, overall_pollen_level + random.randint(0, 2)),
                "mold": min(10, overall_pollen_level),
                "grass": max(1, overall_pollen_level - random.randint(1, 3))
            }
        # Winter (December-February): Generally low pollen, mold can be present
        else:
            active_pollen_types = ["mold", "indoor"]
            # Mold can be present year-round
            pollen_levels = {
                "mold": max(1, overall_pollen_level - 1),
                "indoor": max(1, overall_pollen_level - 2)
            }
            
        # Generate recommendations based on pollen level and types
        recommendations = []
        
        if overall_pollen_level > 6:
            recommendations.append("Keep windows closed to prevent pollen from entering your home.")
            recommendations.append("Use air purifiers indoors to reduce airborne pollen.")
            recommendations.append("Consider wearing a mask when outdoors for extended periods.")
            
            if "tree" in active_pollen_types and pollen_levels["tree"] > 6:
                recommendations.append("Tree pollen is high. Limit exposure to wooded areas.")
            
            if "grass" in active_pollen_types and pollen_levels["grass"] > 6:
                recommendations.append("Grass pollen is high. Avoid freshly cut lawns.")
                
            if "weed" in active_pollen_types and pollen_levels["weed"] > 6:
                recommendations.append("Weed pollen is high. Be cautious in areas with unmanaged vegetation.")
                
            if "mold" in active_pollen_types and pollen_levels["mold"] > 6:
                recommendations.append("Mold spores are high. Be cautious in damp outdoor areas.")
                
        elif overall_pollen_level > 3:
            recommendations.append("Consider taking preventative allergy medication.")
            recommendations.append("Shower after spending time outdoors to wash off pollen.")
            
            if "indoor" in active_pollen_types and pollen_levels["indoor"] > 3:
                recommendations.append("Indoor allergens may be elevated. Keep your home clean and dust-free.")
        else:
            recommendations.append("Pollen levels are low. Good time for outdoor activities for allergy sufferers.")
            
        # Generate 7-day forecast with realistic variations
        forecast = []
        for i in range(1, 8):
            forecast_date = date + datetime.timedelta(days=i)
            # Create realistic variations (±30% with trend smoothing)
            if i <= 3:
                # Short term: less variation
                variation = random.uniform(0.85, 1.15)
            else:
                # Longer term: more variation
                variation = random.uniform(0.7, 1.3)
                
            # Smooth the variations to create trends rather than random jumps
            if i > 1:
                # Blend with previous day for smoothness
                previous_level = forecast[i-2]["level"]
                forecasted_level = round(max(1, min(10, overall_pollen_level * variation * 0.7 + previous_level * 0.3)))
            else:
                forecasted_level = round(max(1, min(10, overall_pollen_level * variation)))
                
            forecast.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "level": forecasted_level
            })
            
        return {
            "overall_level": overall_pollen_level,
            "level_category": category,
            "level_description": description,
            "alert_type": alert_type,
            "active_pollen_types": active_pollen_types,
            "pollen_levels": pollen_levels,
            "recommendations": recommendations,
            "forecast": forecast
        }
    except Exception as e:
        logger.error(f"Error getting pollen count for {city}: {e}")
        return {
            "overall_level": 3,
            "level_category": "Moderate",
            "level_description": "Could not get precise pollen data.",
            "alert_type": "info",
            "active_pollen_types": ["tree", "grass"],
            "pollen_levels": {"tree": 3, "grass": 3},
            "recommendations": ["Keep windows closed during high pollen days.", 
                                "Check local pollen forecasts regularly."],
            "forecast": []
        }

def get_uv_index(city: str, date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """
    Get UV index for a specific city and date
    
    Args:
        city (str): City name
        date (datetime, optional): Date for UV index. Defaults to current date.
        
    Returns:
        dict: UV index data
    """
    try:
        if date is None:
            date = datetime.datetime.now()
            
        # Get weather data
        weather_data = weather_utils.get_city_weather(city)
        
        # Base UV index on weather and seasonal factors
        clouds = weather_data.get('clouds', {}).get('all', 50)  # Cloud coverage (%)
        weather_condition = weather_data.get('weather', [{}])[0].get('main', '').lower()
        
        # Get coordinates for solar intensity calculation
        lat = weather_data.get('coord', {}).get('lat', 0)
        lon = weather_data.get('coord', {}).get('lon', 0)
        
        # Seasonal factor based on month
        month = date.month
        seasonal_factor = 1.0
        
        # Northern hemisphere seasons
        if lat >= 0:
            if 5 <= month <= 8:  # Summer
                seasonal_factor = 1.5
            elif month in [4, 9]:  # Late spring, early fall
                seasonal_factor = 1.2
            elif month in [3, 10]:  # Early spring, late fall
                seasonal_factor = 0.8
            else:  # Winter
                seasonal_factor = 0.5
        # Southern hemisphere seasons (reversed)
        else:
            if 11 <= month <= 12 or 1 <= month <= 2:  # Summer
                seasonal_factor = 1.5
            elif month in [3, 10]:  # Late spring, early fall
                seasonal_factor = 1.2
            elif month in [4, 9]:  # Early spring, late fall
                seasonal_factor = 0.8
            else:  # Winter
                seasonal_factor = 0.5
                
        # Base UV level (0-11 scale)
        base_uv = 6 * seasonal_factor  # Mid-range starting point
        
        # Adjust for cloud coverage
        cloud_factor = 1.0 - (clouds / 100.0) * 0.8  # Clouds can block up to 80% of UV
        
        # Adjust for weather conditions
        weather_factor = 1.0
        if 'rain' in weather_condition or 'drizzle' in weather_condition:
            weather_factor = 0.7  # Rain reduces UV
        elif 'snow' in weather_condition:
            weather_factor = 0.6  # Snow reduces UV
        elif 'thunderstorm' in weather_condition:
            weather_factor = 0.5  # Heavy clouds and rain in thunderstorms
        elif 'clear' in weather_condition:
            weather_factor = 1.2  # Clear skies increase UV
            
        # Calculate final UV index
        uv_index = round(base_uv * cloud_factor * weather_factor)
        
        # Ensure within scale (0-11+)
        uv_index = max(0, min(12, uv_index))
        
        # UV index categories
        if uv_index <= 2:
            category = "Low"
            description = "Low danger from the sun's UV rays."
            color = "#299501"  # Green
            protection_needed = "No protection needed."
            alert_type = "success"
        elif uv_index <= 5:
            category = "Moderate"
            description = "Moderate risk of harm from unprotected sun exposure."
            color = "#F7E401"  # Yellow
            protection_needed = "Wear sunscreen and protective clothing."
            alert_type = "info"
        elif uv_index <= 7:
            category = "High"
            description = "High risk of harm from unprotected sun exposure."
            color = "#F85900"  # Orange
            protection_needed = "Wear SPF 30+ sunscreen, a hat, and sunglasses."
            alert_type = "warning"
        elif uv_index <= 10:
            category = "Very High"
            description = "Very high risk of harm from unprotected sun exposure."
            color = "#D8001D"  # Red
            protection_needed = "Seek shade during midday hours, wear protective clothing."
            alert_type = "danger"
        else:
            category = "Extreme"
            description = "Extreme risk of harm from unprotected sun exposure."
            color = "#6B49C8"  # Purple
            protection_needed = "Avoid being outside during midday hours."
            alert_type = "danger"
            
        # Generate recommendations based on UV index
        recommendations = []
        
        if uv_index > 2:
            recommendations.append("Apply sunscreen with SPF appropriate for your skin type.")
            
            if uv_index > 5:
                recommendations.append("Wear protective clothing, a wide-brimmed hat, and UV-blocking sunglasses.")
                recommendations.append("Seek shade between 10am and 4pm when UV is strongest.")
                
                if uv_index > 7:
                    recommendations.append("Reapply sunscreen every 2 hours, especially after swimming or sweating.")
                    recommendations.append("Consider UV-protective clothing with UPF rating.")
                    
                    if uv_index > 10:
                        recommendations.append("Minimize outdoor activities during midday hours.")
                        recommendations.append("Check for UV alerts in your weather forecasts.")
        else:
            recommendations.append("You can safely stay outside with minimal protection.")
            
        # Generate 7-day forecast with realistic variations
        forecast = []
        for i in range(1, 8):
            forecast_date = date + datetime.timedelta(days=i)
            # Create realistic variations (±20% with seasonal trend)
            if i <= 3:
                # Short term: less variation
                variation = random.uniform(0.9, 1.1)
            else:
                # Longer term: more variation
                variation = random.uniform(0.8, 1.2)
                
            # Smooth the variations to create trends
            if i > 1:
                # Blend with previous day for smoothness
                previous_uv = forecast[i-2]["uv_index"]
                forecasted_uv = round(max(0, min(12, uv_index * variation * 0.7 + previous_uv * 0.3)))
            else:
                forecasted_uv = round(max(0, min(12, uv_index * variation)))
                
            forecast.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "uv_index": forecasted_uv
            })
            
        return {
            "uv_index": uv_index,
            "category": category,
            "description": description,
            "color": color,
            "protection_needed": protection_needed,
            "alert_type": alert_type,
            "recommendations": recommendations,
            "forecast": forecast
        }
    except Exception as e:
        logger.error(f"Error getting UV index for {city}: {e}")
        return {
            "uv_index": 4,
            "category": "Moderate",
            "description": "Moderate risk of harm from unprotected sun exposure.",
            "color": "#F7E401",
            "protection_needed": "Wear sunscreen and protective clothing.",
            "alert_type": "info",
            "recommendations": ["Apply sunscreen with SPF appropriate for your skin type.",
                               "Wear protective clothing, a hat, and sunglasses."],
            "forecast": []
        }

def get_cold_flu_risk(city: str, date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
    """
    Get cold and flu risk assessment for a specific city
    
    Args:
        city (str): City name
        date (datetime, optional): Date for cold/flu risk. Defaults to current date.
        
    Returns:
        dict: Cold and flu risk data
    """
    try:
        if date is None:
            date = datetime.datetime.now()
            
        # Get weather data
        weather_data = weather_utils.get_city_weather(city)
        
        # Factors affecting cold/flu risk
        temperature = weather_data.get('main', {}).get('temp', 20)
        humidity = weather_data.get('main', {}).get('humidity', 50)
        
        # Base risk on weather, seasonal, and other factors
        # Temperature: Cold weather tends to increase risk
        temp_factor = 0
        if temperature < 0:
            temp_factor = 3  # Very cold
        elif temperature < 10:
            temp_factor = 2  # Cold
        elif temperature < 20:
            temp_factor = 1  # Cool
        else:
            temp_factor = 0  # Warm or hot
            
        # Humidity: Very dry or very humid conditions can increase risk
        humidity_factor = 0
        if humidity < 30:
            humidity_factor = 2  # Very dry
        elif humidity > 80:
            humidity_factor = 1  # Very humid
        else:
            humidity_factor = 0  # Moderate humidity
            
        # Seasonal factor
        month = date.month
        seasonal_factor = 0
        
        # Northern hemisphere flu season
        if 10 <= month <= 12 or 1 <= month <= 3:
            seasonal_factor = 3  # Peak flu season
        elif month in [4, 9]:
            seasonal_factor = 2  # Shoulder season
        elif month in [5, 8]:
            seasonal_factor = 1  # Low season
        else:
            seasonal_factor = 0  # Summer, minimal flu
            
        # Calculate overall risk (1-10 scale)
        base_risk = temp_factor + humidity_factor + seasonal_factor
        
        # Add some randomness to represent local outbreaks, etc.
        random_factor = random.randint(0, 2)
        
        risk_value = base_risk + random_factor
        
        # Ensure within scale (1-10)
        risk_value = max(1, min(10, risk_value))
        
        # Risk categories
        if risk_value <= 3:
            category = "Low"
            description = "Low risk of cold and flu in your area."
            alert_type = "success"
        elif risk_value <= 6:
            category = "Moderate"
            description = "Moderate risk of cold and flu in your area."
            alert_type = "info"
        elif risk_value <= 8:
            category = "High"
            description = "High risk of cold and flu in your area."
            alert_type = "warning"
        else:
            category = "Very High"
            description = "Very high risk of cold and flu in your area."
            alert_type = "danger"
            
        # Generate symptoms to watch for
        symptoms = []
        if risk_value > 3:
            symptoms = [
                "Fever or feeling feverish/chills",
                "Cough",
                "Sore throat",
                "Runny or stuffy nose",
                "Muscle or body aches",
                "Headaches",
                "Fatigue (tiredness)"
            ]
            
        # Generate recommendations based on risk level
        recommendations = []
        
        if risk_value > 6:
            recommendations.append("Wash hands frequently with soap and water for at least 20 seconds.")
            recommendations.append("Avoid close contact with people who are sick.")
            recommendations.append("Consider wearing a mask in crowded indoor spaces.")
            recommendations.append("Get your seasonal flu vaccination if you haven't already.")
            recommendations.append("Boost your immune system with vitamin-rich foods and sufficient sleep.")
            
            if risk_value > 8:
                recommendations.append("Avoid unnecessary travel to high-risk areas.")
                recommendations.append("Consider limiting time in crowded public places.")
                recommendations.append("Keep sanitizer with you when out in public.")
        elif risk_value > 3:
            recommendations.append("Wash hands regularly, especially before eating.")
            recommendations.append("Avoid touching your face, eyes, nose, and mouth.")
            recommendations.append("Consider getting a flu shot if you haven't already.")
        else:
            recommendations.append("Practice normal hygiene like regular handwashing.")
            recommendations.append("Stay home if you feel unwell to prevent spreading illness.")
            
        # Generate 7-day forecast with realistic variations
        forecast = []
        for i in range(1, 8):
            forecast_date = date + datetime.timedelta(days=i)
            # Create realistic variations (±20% with trend smoothing)
            if i <= 3:
                # Short term: less variation
                variation = random.uniform(0.9, 1.1)
            else:
                # Longer term: more variation
                variation = random.uniform(0.8, 1.2)
                
            # Smooth the variations to create trends
            if i > 1:
                # Blend with previous day for smoothness
                previous_risk = forecast[i-2]["risk"]
                forecasted_risk = round(max(1, min(10, risk_value * variation * 0.7 + previous_risk * 0.3)))
            else:
                forecasted_risk = round(max(1, min(10, risk_value * variation)))
                
            forecast.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "risk": forecasted_risk
            })
            
        return {
            "risk_value": risk_value,
            "risk_category": category,
            "risk_description": description,
            "alert_type": alert_type,
            "symptoms": symptoms,
            "recommendations": recommendations,
            "forecast": forecast
        }
    except Exception as e:
        logger.error(f"Error getting cold/flu risk for {city}: {e}")
        return {
            "risk_value": 4,
            "risk_category": "Moderate",
            "risk_description": "Moderate risk of cold and flu in your area.",
            "alert_type": "info",
            "symptoms": ["Fever or feeling feverish/chills", "Cough", "Sore throat"],
            "recommendations": ["Wash hands regularly, especially before eating.",
                               "Avoid touching your face, eyes, nose, and mouth."],
            "forecast": []
        }

def get_air_quality_health_risk(city: str, health_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get air quality health risk assessment for a specific city and health profile
    
    Args:
        city (str): City name
        health_profile (dict, optional): User health profile. Defaults to None.
        
    Returns:
        dict: Air quality health risk data
    """
    try:
        # Get air quality data
        aqi_data = api_utils.get_city_air_quality(city)
        
        # Get AQI value
        aqi = aqi_data.get('aqi', 50)
        
        # Default health profile if none provided
        if health_profile is None:
            health_profile = {
                'health_concerns': [],
                'activity_level': 'moderate',
                'age_group': 'adult'
            }
            
        # Get standard AQI category
        aqi_category = health_utils.get_aqi_category(aqi)
        
        # Determine personalized risk based on health profile
        health_concerns = health_profile.get('health_concerns', [])
        activity_level = health_profile.get('activity_level', 'moderate')
        age_group = health_profile.get('age_group', 'adult')
        
        # Adjust risk based on health concerns
        risk_adjustment = 0
        
        if 'asthma' in health_concerns:
            risk_adjustment += 1
        if 'copd' in health_concerns:
            risk_adjustment += 2
        if 'heart_disease' in health_concerns:
            risk_adjustment += 1
        if 'allergies' in health_concerns:
            risk_adjustment += 1
            
        # Adjust risk based on activity level
        if activity_level == 'high':
            risk_adjustment += 1
        elif activity_level == 'low':
            risk_adjustment -= 1
            
        # Adjust risk based on age group
        if age_group == 'child' or age_group == 'senior':
            risk_adjustment += 1
            
        # Determine personalized health risk category
        personalized_category = aqi_category
        personalized_alert_type = 'success'
        
        if aqi_category == 'Good':
            if risk_adjustment >= 3:
                personalized_category = 'Moderate'
                personalized_alert_type = 'info'
            else:
                personalized_category = 'Good'
                personalized_alert_type = 'success'
        elif aqi_category == 'Moderate':
            if risk_adjustment >= 2:
                personalized_category = 'Unhealthy for Sensitive Groups'
                personalized_alert_type = 'warning'
            else:
                personalized_category = 'Moderate'
                personalized_alert_type = 'info'
        elif aqi_category == 'Unhealthy for Sensitive Groups':
            if risk_adjustment >= 1:
                personalized_category = 'Unhealthy'
                personalized_alert_type = 'danger'
            else:
                personalized_category = 'Unhealthy for Sensitive Groups'
                personalized_alert_type = 'warning'
        elif aqi_category == 'Unhealthy':
            personalized_category = 'Unhealthy'
            personalized_alert_type = 'danger'
        elif aqi_category == 'Very Unhealthy' or aqi_category == 'Hazardous':
            personalized_category = 'Hazardous'
            personalized_alert_type = 'danger'
            
        # Generate recommendations based on air quality and health profile
        recommendations = []
        
        # Basic recommendations based on AQI
        if aqi > 150:  # Unhealthy or worse
            recommendations.append("Avoid outdoor activities and exercise.")
            recommendations.append("Keep windows and doors closed.")
            recommendations.append("Use air purifiers indoors if available.")
            
            if aqi > 200:  # Very Unhealthy or worse
                recommendations.append("Wear N95 masks if you must go outside.")
                recommendations.append("Reconsider travel plans in the area.")
        elif aqi > 100:  # Unhealthy for Sensitive Groups
            recommendations.append("Reduce prolonged or heavy outdoor exertion.")
            recommendations.append("Take more breaks during outdoor activities.")
            recommendations.append("Watch for symptoms like coughing or shortness of breath.")
        elif aqi > 50:  # Moderate
            recommendations.append("Unusually sensitive individuals should consider reducing prolonged outdoor exertion.")
        else:  # Good
            recommendations.append("Air quality is good. It's a great day for outdoor activities.")
            
        # Personalized recommendations based on health profile
        if 'asthma' in health_concerns:
            if aqi > 50:
                recommendations.append("Asthma sufferers: Keep rescue inhaler nearby.")
            if aqi > 100:
                recommendations.append("Asthma sufferers: Consider staying indoors with air filtration.")
                
        if 'copd' in health_concerns:
            if aqi > 50:
                recommendations.append("COPD sufferers: Monitor breathing closely and limit outdoor exposure.")
            if aqi > 100:
                recommendations.append("COPD sufferers: Stay indoors and ensure medications are available.")
                
        if 'heart_disease' in health_concerns:
            if aqi > 100:
                recommendations.append("Heart disease patients: Avoid strenuous activities outdoors.")
                
        if 'allergies' in health_concerns:
            if aqi > 50:
                recommendations.append("Allergy sufferers: Consider taking antihistamines before going outside.")
                
        # Activity-specific recommendations
        if activity_level == 'high':
            if aqi > 50:
                recommendations.append("Consider moving intensive exercise indoors or reducing intensity.")
            if aqi > 100:
                recommendations.append("Reschedule outdoor workouts or competitions to a day with better air quality.")
                
        # Age-specific recommendations
        if age_group == 'child':
            if aqi > 100:
                recommendations.append("Children should limit outdoor play time.")
        elif age_group == 'senior':
            if aqi > 100:
                recommendations.append("Seniors should stay indoors and keep windows closed.")
                
        # Remove any duplicate recommendations
        recommendations = list(dict.fromkeys(recommendations))
            
        return {
            "aqi": aqi,
            "aqi_category": personalized_category,
            "alert_type": personalized_alert_type,
            "recommendations": recommendations,
            "pollutants": aqi_data.get('pollutants', {}),
            "main_pollutant": health_utils.get_main_pollutant(aqi_data.get('pollutants', {}))
        }
    except Exception as e:
        logger.error(f"Error getting air quality health risk for {city}: {e}")
        return {
            "aqi": 50,
            "aqi_category": "Moderate",
            "alert_type": "info",
            "recommendations": [
                "Unusually sensitive individuals should consider reducing prolonged outdoor exertion.",
                "Watch for symptoms like coughing or shortness of breath.",
                "Check local air quality forecasts for updates."
            ],
            "pollutants": {},
            "main_pollutant": "PM2.5"
        }

def get_comprehensive_health_alerts(city: str, health_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get comprehensive health alerts for a specific city combining air quality, pollen, UV, and cold/flu data
    
    Args:
        city (str): City name
        health_profile (dict, optional): User health profile. Defaults to None.
        
    Returns:
        dict: Comprehensive health alerts
    """
    try:
        # Get individual health alerts
        air_quality = get_air_quality_health_risk(city, health_profile)
        pollen = get_pollen_count(city)
        uv_index = get_uv_index(city)
        cold_flu = get_cold_flu_risk(city)
        
        # Determine primary alert based on severity
        primary_alert = None
        
        # Air quality alert
        if air_quality["alert_type"] == "danger":
            primary_alert = {
                "type": "air_quality",
                "alert_type": "danger",
                "message": f"Air Quality Alert: {air_quality['aqi_category']} air quality ({air_quality['aqi']} AQI). {air_quality['recommendations'][0] if air_quality['recommendations'] else ''}"
            }
        elif air_quality["alert_type"] == "warning" and not primary_alert:
            primary_alert = {
                "type": "air_quality",
                "alert_type": "warning",
                "message": f"Air Quality Alert: {air_quality['aqi_category']} air quality ({air_quality['aqi']} AQI). {air_quality['recommendations'][0] if air_quality['recommendations'] else ''}"
            }
            
        # UV alert
        if uv_index["alert_type"] == "danger" and (not primary_alert or primary_alert["alert_type"] != "danger"):
            primary_alert = {
                "type": "uv",
                "alert_type": "danger",
                "message": f"UV Alert: {uv_index['category']} UV index ({uv_index['uv_index']}). {uv_index['protection_needed']}"
            }
        elif uv_index["alert_type"] == "warning" and not primary_alert:
            primary_alert = {
                "type": "uv",
                "alert_type": "warning",
                "message": f"UV Alert: {uv_index['category']} UV index ({uv_index['uv_index']}). {uv_index['protection_needed']}"
            }
            
        # Pollen alert
        if pollen["alert_type"] == "danger" and (not primary_alert or primary_alert["alert_type"] != "danger"):
            primary_alert = {
                "type": "pollen",
                "alert_type": "danger",
                "message": f"Pollen Alert: {pollen['level_category']} pollen levels today. {pollen['recommendations'][0] if pollen['recommendations'] else ''}"
            }
        elif pollen["alert_type"] == "warning" and not primary_alert:
            primary_alert = {
                "type": "pollen",
                "alert_type": "warning",
                "message": f"Pollen Alert: {pollen['level_category']} pollen levels today. {pollen['recommendations'][0] if pollen['recommendations'] else ''}"
            }
            
        # Cold/flu alert
        if cold_flu["alert_type"] == "danger" and (not primary_alert or primary_alert["alert_type"] != "danger"):
            primary_alert = {
                "type": "cold_flu",
                "alert_type": "danger",
                "message": f"Cold & Flu Alert: {cold_flu['risk_category']} risk in your area. {cold_flu['recommendations'][0] if cold_flu['recommendations'] else ''}"
            }
        elif cold_flu["alert_type"] == "warning" and not primary_alert:
            primary_alert = {
                "type": "cold_flu",
                "alert_type": "warning",
                "message": f"Cold & Flu Alert: {cold_flu['risk_category']} risk in your area. {cold_flu['recommendations'][0] if cold_flu['recommendations'] else ''}"
            }
            
        # If no severe alerts, create an informational alert
        if not primary_alert:
            # Find the most important info alert
            if air_quality["alert_type"] == "info":
                primary_alert = {
                    "type": "air_quality",
                    "alert_type": "info",
                    "message": f"Air Quality: {air_quality['aqi_category']} air quality today in {city}."
                }
            elif pollen["alert_type"] == "info":
                primary_alert = {
                    "type": "pollen",
                    "alert_type": "info",
                    "message": f"Pollen Levels: {pollen['level_category']} pollen levels today in {city}."
                }
            elif uv_index["alert_type"] == "info":
                primary_alert = {
                    "type": "uv",
                    "alert_type": "info",
                    "message": f"UV Index: {uv_index['category']} UV levels today in {city}."
                }
            elif cold_flu["alert_type"] == "info":
                primary_alert = {
                    "type": "cold_flu",
                    "alert_type": "info",
                    "message": f"Cold & Flu: {cold_flu['risk_category']} risk today in {city}."
                }
            else:
                # Default good conditions message
                primary_alert = {
                    "type": "general",
                    "alert_type": "success",
                    "message": f"Good news! Environmental conditions in {city} are favorable today. Enjoy your outdoor activities."
                }
                
        # Create personalized recommendations combining all alert types
        recommendations = []
        
        # Get health concerns for personalization
        health_concerns = health_profile.get('health_concerns', []) if health_profile else []
        
        # Add personalized recommendations based on health concerns
        if 'asthma' in health_concerns:
            if air_quality['aqi'] > 100 or pollen['overall_level'] > 6:
                recommendations.append(f"With your asthma, be extra cautious today with {air_quality['aqi_category']} air quality and {pollen['level_category']} pollen levels.")
                
        if 'allergies' in health_concerns:
            if pollen['overall_level'] > 4:
                recommendations.append(f"Given your allergies, take preventative medication today as pollen levels are {pollen['level_category']}.")
                
        if 'heart_disease' in health_concerns:
            if air_quality['aqi'] > 100 or cold_flu['risk_value'] > 6:
                recommendations.append("With your heart condition, limit outdoor activities today due to environmental conditions.")
                
        if 'copd' in health_concerns:
            if air_quality['aqi'] > 50:
                recommendations.append("With COPD, you should be particularly careful about current air quality conditions.")
                
        # Add the most important recommendations from each category
        for rec_list, count in [
            (air_quality['recommendations'], 2),
            (pollen['recommendations'], 1),
            (uv_index['recommendations'], 1),
            (cold_flu['recommendations'], 1)
        ]:
            if rec_list:
                for rec in rec_list[:count]:
                    if rec not in recommendations:
                        recommendations.append(rec)
                        
        # Remove any duplicate recommendations
        recommendations = list(dict.fromkeys(recommendations))
            
        return {
            "primary_alert": primary_alert,
            "air_quality": air_quality,
            "pollen": pollen,
            "uv_index": uv_index,
            "cold_flu": cold_flu,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Error getting comprehensive health alerts for {city}: {e}")
        return {
            "primary_alert": {
                "type": "general",
                "alert_type": "info",
                "message": f"Health alerts service is experiencing some issues. Please check individual health indicators for {city}."
            },
            "air_quality": get_air_quality_health_risk(city, health_profile),
            "pollen": get_pollen_count(city),
            "uv_index": get_uv_index(city),
            "cold_flu": get_cold_flu_risk(city),
            "recommendations": ["Check local forecasts for the most up-to-date health information."]
        }