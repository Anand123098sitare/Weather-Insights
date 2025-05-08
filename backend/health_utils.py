import logging
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_aqi_category(aqi_value):
    """
    Determine AQI category based on AQI value
    
    Args:
        aqi_value (float): AQI value
        
    Returns:
        str: AQI category
    """
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

def get_health_recommendations(aqi_data, health_profile):
    """
    Generate personalized health recommendations based on air quality and health profile
    
    Args:
        aqi_data (dict): Air quality data including AQI value
        health_profile (dict): User health profile including health concerns and activity level
    
    Returns:
        dict: Personalized health recommendations
    """
    try:
        aqi_value = aqi_data.get('aqi', 0)
        aqi_category = get_aqi_category(aqi_value)
        
        # Get health concerns from profile
        health_concerns = health_profile.get('health_concerns', [])
        activity_level = health_profile.get('activity_level', 'moderate')
        age_group = health_profile.get('age_group', 'adult')
        
        # Base recommendations
        base_recommendations = {
            "Good": {
                "general": "Air quality is good. It's a great day for outdoor activities.",
                "sensitive": "Air quality is good. Most people won't be affected."
            },
            "Moderate": {
                "general": "Air quality is acceptable. Consider reducing prolonged outdoor exertion if you are sensitive to air pollution.",
                "sensitive": "If you have respiratory issues, consider limiting prolonged outdoor activities."
            },
            "Unhealthy for Sensitive Groups": {
                "general": "Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
                "sensitive": "Reduce prolonged or heavy outdoor exertion. Take more breaks during outdoor activities."
            },
            "Unhealthy": {
                "general": "Everyone may begin to experience health effects. Members of sensitive groups may experience more serious effects.",
                "sensitive": "Avoid prolonged or heavy outdoor exertion. Move activities indoors or reschedule to a time when air quality is better."
            },
            "Very Unhealthy": {
                "general": "Health warnings of emergency conditions. The entire population is more likely to be affected.",
                "sensitive": "Avoid all outdoor physical activity. Stay indoors and keep windows closed."
            },
            "Hazardous": {
                "general": "Health alert: everyone may experience more serious health effects. Avoid all outdoor activities.",
                "sensitive": "Remain indoors and keep activity levels low. Close windows and use air purifiers if available."
            }
        }
        
        # Determine if user is in sensitive group
        is_sensitive = len(health_concerns) > 0 or age_group in ['child', 'senior']
        
        # Get appropriate recommendation
        general_advice = base_recommendations[aqi_category]["sensitive" if is_sensitive else "general"]
        
        # Specific recommendations based on health concerns
        specific_recommendations = []
        if "asthma" in health_concerns:
            if aqi_category in ["Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy", "Hazardous"]:
                specific_recommendations.append("Keep your rescue inhaler with you at all times.")
            if aqi_category in ["Very Unhealthy", "Hazardous"]:
                specific_recommendations.append("Consider preemptive use of prescribed asthma medications.")
                
        if "heart_disease" in health_concerns:
            if aqi_category in ["Unhealthy", "Very Unhealthy", "Hazardous"]:
                specific_recommendations.append("Limit physical exertion to reduce strain on your heart.")
            if aqi_category in ["Very Unhealthy", "Hazardous"]:
                specific_recommendations.append("Monitor for symptoms like chest pain, shortness of breath, or unusual fatigue.")
                
        if "copd" in health_concerns:
            if aqi_category in ["Moderate", "Unhealthy for Sensitive Groups", "Unhealthy"]:
                specific_recommendations.append("Use your oxygen as prescribed and consider increasing flow rate if needed.")
            if aqi_category in ["Very Unhealthy", "Hazardous"]:
                specific_recommendations.append("Stay indoors with windows closed and use air purifiers if available.")
                
        # Activity recommendations based on activity level
        activity_recommendations = []
        if activity_level == "high":
            if aqi_category in ["Moderate"]:
                activity_recommendations.append("Consider reducing the intensity of outdoor workouts.")
            elif aqi_category in ["Unhealthy for Sensitive Groups"]:
                activity_recommendations.append("Shorten outdoor workouts or exercise indoors.")
            elif aqi_category in ["Unhealthy", "Very Unhealthy", "Hazardous"]:
                activity_recommendations.append("Move all workouts indoors.")
        elif activity_level == "moderate":
            if aqi_category in ["Unhealthy for Sensitive Groups"]:
                activity_recommendations.append("Consider reducing time spent outdoors.")
            elif aqi_category in ["Unhealthy", "Very Unhealthy", "Hazardous"]:
                activity_recommendations.append("Limit outdoor activities and exercise indoors.")
        
        # Age-specific recommendations
        age_recommendations = []
        if age_group == "child":
            if aqi_category in ["Unhealthy for Sensitive Groups"]:
                age_recommendations.append("Children should take more breaks during outdoor play.")
            elif aqi_category in ["Unhealthy", "Very Unhealthy", "Hazardous"]:
                age_recommendations.append("Children should play indoors.")
        elif age_group == "senior":
            if aqi_category in ["Moderate", "Unhealthy for Sensitive Groups"]:
                age_recommendations.append("Seniors should limit prolonged outdoor activities.")
            elif aqi_category in ["Unhealthy", "Very Unhealthy", "Hazardous"]:
                age_recommendations.append("Seniors should stay indoors and keep activity levels light.")
        
        # Generate history and forecast
        history_data = generate_mock_history_data(aqi_value)
        
        # Main pollutant
        main_pollutant = aqi_data.get('main_pollutant', 'PM2.5')
        
        # Combine all recommendations
        return {
            "aqi_value": aqi_value,
            "aqi_category": aqi_category,
            "general_advice": general_advice,
            "specific_recommendations": specific_recommendations,
            "activity_recommendations": activity_recommendations,
            "age_recommendations": age_recommendations,
            "history": history_data,
            "main_pollutant": main_pollutant,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating health recommendations: {e}")
        return {
            "error": "Failed to generate recommendations",
            "timestamp": datetime.now().isoformat()
        }

def generate_mock_history_data(aqi_value, days=7):
    """
    Generate mock historical AQI data based on current AQI
    
    Args:
        aqi_value (float): Current AQI value
        days (int): Number of days of history to generate
    
    Returns:
        list: List of daily AQI values with dates
    """
    try:
        history = []
        base_value = aqi_value
        
        for i in range(days, 0, -1):
            # Calculate date for this history point
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            
            # Generate a value with some randomness around the base
            # The variance increases for further back dates
            variance = (i / days) * 0.3 * base_value
            value = base_value + random.uniform(-variance, variance)
            value = max(0, round(value, 1))  # Ensure non-negative and round to 1 decimal
            
            history.append({
                "date": date,
                "value": value,
                "category": get_aqi_category(value)
            })
            
            # Slightly adjust the base value for the next day
            base_value = value + random.uniform(-0.1 * value, 0.1 * value)
            
        return history
    except Exception as e:
        logger.error(f"Error generating mock history data: {e}")
        return []

def get_main_pollutant(pollutants):
    """
    Determine the main pollutant from a dictionary of pollutants
    
    Args:
        pollutants (dict): Dictionary of pollutants with their values
    
    Returns:
        str: Name of the main pollutant
    """
    try:
        # Find the pollutant with the highest value
        max_pollutant = None
        max_value = 0
        
        for pollutant, value in pollutants.items():
            if value > max_value:
                max_value = value
                max_pollutant = pollutant
        
        return max_pollutant if max_pollutant else "PM2.5"
    except Exception as e:
        logger.error(f"Error determining main pollutant: {e}")
        return "PM2.5"