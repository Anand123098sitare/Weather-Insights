"""
Smart Notifications Utilities

This module provides utilities for generating intelligent, context-aware weather notifications
and activity recommendations based on forecast data.
"""
import logging
import json
import random
import datetime
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from backend import weather_utils
from backend import agriculture_utils

logger = logging.getLogger(__name__)

# Activity types and their ideal weather conditions
ACTIVITIES = {
    "outdoor_painting": {
        "ideal_conditions": {
            "rain": False,
            "humidity_range": (20, 60),
            "temp_range": (15, 28),
            "wind_speed_max": 15,  # km/h
        },
        "notifications": [
            "Dry spell alert: No rain expected for {days} days — good week for outdoor painting.",
            "Perfect painting weather ahead: {days} consecutive dry days with mild temperatures.",
            "Great opportunity for outdoor painting projects this week with {days} rain-free days ahead."
        ]
    },
    "gardening": {
        "ideal_conditions": {
            "rain": False,
            "temp_range": (15, 30),
            "wind_speed_max": 20,  # km/h
        },
        "notifications": [
            "Garden-friendly forecast: Mild temperatures and no heavy rain for the next {days} days.",
            "Ideal gardening window: {days} days of favorable conditions ahead for planting and maintenance.",
            "Green thumb alert: Perfect weather for garden projects over the next {days} days."
        ]
    },
    "hiking": {
        "ideal_conditions": {
            "rain": False,
            "temp_range": (12, 27),
            "wind_speed_max": 25,  # km/h
        },
        "notifications": [
            "Trail conditions looking great: {days} days of hiking-friendly weather ahead.",
            "Hiking forecast: Clear skies and comfortable temperatures for the next {days} days.",
            "Outdoor adventure alert: Excellent hiking conditions expected for {days} consecutive days."
        ]
    },
    "beach_day": {
        "ideal_conditions": {
            "rain": False,
            "temp_range": (25, 35),
            "cloud_cover_max": 30,  # percent
        },
        "notifications": [
            "Beach weather alert: {days} days of sunshine and warm temperatures perfect for the shore.",
            "Sun and sand forecast: Ideal beach conditions for the next {days} days.",
            "Pack your beach gear: {days} days of perfect beach weather ahead."
        ]
    },
    "laundry_drying": {
        "ideal_conditions": {
            "rain": False,
            "humidity_range": (30, 60),
            "temp_range": (15, 35),
        },
        "notifications": [
            "Laundry-friendly forecast: Great drying conditions for the next {days} days.",
            "Efficient drying alert: {days} consecutive days optimal for air-drying laundry.",
            "Energy-saving opportunity: Perfect natural drying conditions for {days} days."
        ]
    },
    "cycling": {
        "ideal_conditions": {
            "rain": False,
            "temp_range": (13, 28),
            "wind_speed_max": 20,  # km/h
        },
        "notifications": [
            "Cycling weather alert: {days} days of ideal riding conditions ahead.",
            "Perfect for pedaling: {days} consecutive days of cyclist-friendly weather expected.",
            "Bike commute forecast: Favorable conditions for the next {days} days."
        ]
    },
    "stargazing": {
        "ideal_conditions": {
            "rain": False,
            "cloud_cover_max": 20,  # percent
            "wind_speed_max": 15,  # km/h
        },
        "night_only": True,
        "notifications": [
            "Stargazing alert: Clear night skies expected for the next {nights} nights.",
            "Astronomy-friendly forecast: {nights} consecutive nights with optimal viewing conditions.",
            "Look up! Perfect stargazing conditions for {nights} nights ahead."
        ]
    },
    "marathon_training": {
        "ideal_conditions": {
            "temp_range": (5, 20),
            "humidity_range": (30, 70),
        },
        "notifications": [
            "Runner's forecast: {days} days of ideal training conditions ahead.",
            "Perfect for marathon training: {days} consecutive days with optimal running weather.",
            "Training opportunity: {days} days of runner-friendly weather expected."
        ]
    }
}

# Weather warnings and their threshold conditions
WEATHER_WARNINGS = {
    "heat_wave": {
        "conditions": {
            "temp_min": 32,  # Celsius
            "consecutive_days": 3,
        },
        "notifications": [
            "Heat wave alert: Temperatures above {temp}°C expected for {days} consecutive days.",
            "Extreme heat warning: {days}-day heat wave with temperatures reaching {temp}°C.",
            "Health alert: Prolonged heat wave with {days} days of temperatures exceeding {temp}°C."
        ]
    },
    "cold_snap": {
        "conditions": {
            "temp_max": 0,  # Celsius
            "consecutive_days": 3,
        },
        "notifications": [
            "Cold snap alert: Temperatures below {temp}°C expected for {days} consecutive days.",
            "Freezing conditions warning: {days}-day cold spell with temperatures dropping to {temp}°C.",
            "Frost alert: Extended period of {days} days with temperatures at or below {temp}°C."
        ]
    },
    "dry_spell": {
        "conditions": {
            "rain_max": 1,  # mm
            "consecutive_days": 7,
        },
        "notifications": [
            "Dry spell alert: Minimal to no rainfall expected for {days} consecutive days.",
            "Drought risk warning: Extended {days}-day period with precipitation below {rain} mm.",
            "Water conservation notice: {days}-day dry spell forecasted with negligible rainfall."
        ]
    },
    "heavy_rain": {
        "conditions": {
            "rain_min": 25,  # mm/day
            "consecutive_days": 2,
        },
        "notifications": [
            "Heavy rain alert: Significant rainfall exceeding {rain} mm/day expected for {days} consecutive days.",
            "Flood risk warning: Prolonged heavy precipitation of {rain}+ mm daily for {days} days.",
            "Drainage alert: Extended period of {days} days with heavy rainfall above {rain} mm daily."
        ]
    },
    "high_wind": {
        "conditions": {
            "wind_min": 40,  # km/h
            "consecutive_days": 1,
        },
        "notifications": [
            "High wind alert: Sustained winds of {wind} km/h or higher expected for {days} days.",
            "Wind hazard warning: Strong winds exceeding {wind} km/h forecasted for {days}-day period.",
            "Outdoor caution: High winds of {wind}+ km/h expected to persist for {days} days."
        ]
    },
    "air_quality": {
        "conditions": {
            "aqi_min": 150,  # AQI value
            "consecutive_days": 1,
        },
        "notifications": [
            "Poor air quality alert: AQI levels exceeding {aqi} expected for {days} days.",
            "Health caution: Unhealthy air quality (AQI {aqi}+) forecasted to continue for {days} days.",
            "Respiratory warning: Elevated pollution levels with AQI above {aqi} for {days}-day period."
        ]
    },
    "high_uv": {
        "conditions": {
            "uv_index_min": 8,  # UV index
            "consecutive_days": 1,
        },
        "notifications": [
            "High UV alert: UV index of {uv} or higher expected for {days} consecutive days.",
            "Sun protection warning: Very high UV levels ({uv}+) forecasted for {days} days.",
            "Skin damage risk: Extreme UV radiation (index {uv}+) continuing for {days} days."
        ]
    }
}

# Calendar-aware special event notifications
SEASONAL_EVENTS = {
    # Format: month, day -> (event_name, notification)
    (3, 20): ("Spring Equinox", [
        "Spring officially begins tomorrow! Expect gradually warming temperatures and increasing daylight.",
        "Welcome spring! Equinox occurs tomorrow with day and night of nearly equal length.",
        "Garden planning alert: Spring equinox tomorrow marks the official start of planting season."
    ]),
    (6, 20): ("Summer Solstice", [
        "Summer officially begins tomorrow with the longest day of the year!",
        "Solstice alert: Tomorrow marks the official start of summer and peak daylight hours.",
        "Seasonal shift: Summer begins tomorrow with the solstice - the longest day of the year."
    ]),
    (9, 22): ("Fall Equinox", [
        "Fall officially begins tomorrow! Expect gradually cooling temperatures and shortening days.",
        "Autumn equinox tomorrow marks the official end of summer with day and night of equal length.",
        "Seasonal transition: Fall begins tomorrow - perfect time for garden cleanup and cool-weather planting."
    ]),
    (12, 21): ("Winter Solstice", [
        "Winter officially begins tomorrow with the shortest day of the year.",
        "Solstice alert: Tomorrow marks the official start of winter and the gradual return of daylight.",
        "Seasonal milestone: Winter begins tomorrow with the solstice - the shortest day of the year."
    ]),
    (4, 22): ("Earth Day", [
        "Earth Day tomorrow! Weather forecast shows {condition} - perfect for outdoor environmental activities.",
        "Earth Day celebration alert: Tomorrow's {condition} weather is ideal for community cleanup events.",
        "Environmental awareness day: Tomorrow's Earth Day forecast shows {condition} conditions."
    ])
}

def get_smart_notifications(city: str, days_ahead: int = 7) -> Dict[str, Any]:
    """
    Generate smart, context-aware notifications based on weather forecast and patterns
    
    Args:
        city (str): City name
        days_ahead (int): Number of days to look ahead for notifications
        
    Returns:
        dict: Smart notifications with varied categories and priority levels
    """
    try:
        # Limit days ahead to a reasonable range
        days_ahead = min(max(days_ahead, 3), 14)
        
        # Get weather forecast
        forecast_data = weather_utils.get_weather_forecast(city)
        current_weather = weather_utils.get_city_weather(city)
        
        # Initialize notification containers
        activity_notifications = []
        warning_notifications = []
        seasonal_notifications = []
        weather_pattern_notifications = []
        agricultural_notifications = []
        
        # Process forecast data into daily summaries
        daily_forecasts = process_forecast_data(forecast_data)
        
        # Generate activity recommendations based on suitable weather patterns
        activity_notifications = generate_activity_notifications(daily_forecasts, days_ahead)
        
        # Generate warning notifications based on extreme or noteworthy conditions
        warning_notifications = generate_warning_notifications(daily_forecasts, days_ahead)
        
        # Generate seasonal and calendar-aware notifications
        seasonal_notifications = generate_seasonal_notifications(daily_forecasts, city)
        
        # Generate notifications based on weather patterns and changes
        weather_pattern_notifications = generate_weather_pattern_notifications(daily_forecasts, current_weather)
        
        # Generate agricultural notifications (garden/plant specific)
        agricultural_notifications = generate_agricultural_notifications(city, daily_forecasts)
        
        # Combine, prioritize and limit notifications
        all_notifications = []
        all_notifications.extend([{"type": "warning", "priority": 1, **notification} for notification in warning_notifications])
        all_notifications.extend([{"type": "activity", "priority": 2, **notification} for notification in activity_notifications])
        all_notifications.extend([{"type": "seasonal", "priority": 3, **notification} for notification in seasonal_notifications])
        all_notifications.extend([{"type": "agricultural", "priority": 3, **notification} for notification in agricultural_notifications])
        all_notifications.extend([{"type": "pattern", "priority": 4, **notification} for notification in weather_pattern_notifications])
        
        # Sort by priority (lower number = higher priority)
        all_notifications.sort(key=lambda x: x["priority"])
        
        # Limit to a reasonable number of notifications (adjust as needed)
        top_notifications = all_notifications[:10]
        
        return {
            "city": city,
            "generated_at": datetime.now().isoformat(),
            "forecast_days": days_ahead,
            "notifications": top_notifications,
            "notification_count": len(top_notifications)
        }
        
    except Exception as e:
        logger.error(f"Error generating smart notifications for {city}: {e}")
        return {
            "city": city,
            "error": str(e),
            "notifications": [
                {
                    "type": "system",
                    "priority": 1,
                    "message": "Weather notification system is currently updating. Check back soon for personalized alerts.",
                    "icon": "sync"
                }
            ],
            "notification_count": 1,
            "generated_at": datetime.now().isoformat()
        }

def process_forecast_data(forecast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process raw forecast data into daily summaries
    
    Args:
        forecast_data (dict): Raw forecast data from weather API
        
    Returns:
        list: Daily forecast summaries
    """
    daily_forecasts = []
    
    # Handle case where forecast data might be missing or incorrectly formatted
    if not forecast_data or 'list' not in forecast_data:
        # Return empty list or generate placeholder data
        return daily_forecasts
    
    # Group forecast periods by day
    forecast_by_day = {}
    for period in forecast_data['list']:
        # Get date from timestamp
        period_time = datetime.fromtimestamp(period['dt'])
        period_date = period_time.date()
        
        if period_date not in forecast_by_day:
            forecast_by_day[period_date] = []
            
        forecast_by_day[period_date].append(period)
    
    # Process each day's forecast into a summary
    for day, periods in sorted(forecast_by_day.items()):
        # Extract relevant data
        temps = [period.get('main', {}).get('temp', 20) for period in periods if 'main' in period]
        humidities = [period.get('main', {}).get('humidity', 50) for period in periods if 'main' in period]
        wind_speeds = [period.get('wind', {}).get('speed', 0) for period in periods if 'wind' in period]
        cloud_covers = [period.get('clouds', {}).get('all', 50) for period in periods if 'clouds' in period]
        
        # Calculate precipitation sum and probability
        precip_sum = 0
        for period in periods:
            if 'rain' in period and '3h' in period['rain']:
                precip_sum += period['rain']['3h']
                
        precip_probs = [period.get('pop', 0) for period in periods if 'pop' in period]
        avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else 0
        
        # Get weather conditions
        weather_ids = [period.get('weather', [{}])[0].get('id', 800) for period in periods if 'weather' in period and len(period['weather']) > 0]
        weather_conditions = [period.get('weather', [{}])[0].get('main', '') for period in periods if 'weather' in period and len(period['weather']) > 0]
        dominant_condition = max(set(weather_conditions), key=weather_conditions.count) if weather_conditions else "Clear"
        
        # Create day summary
        day_summary = {
            "date": day.strftime("%Y-%m-%d"),
            "day_of_week": day.strftime("%A"),
            "min_temp": min(temps) if temps else 20,
            "max_temp": max(temps) if temps else 20,
            "avg_temp": sum(temps) / len(temps) if temps else 20,
            "min_humidity": min(humidities) if humidities else 50,
            "max_humidity": max(humidities) if humidities else 50,
            "avg_humidity": sum(humidities) / len(humidities) if humidities else 50,
            "max_wind_speed": max(wind_speeds) if wind_speeds else 0,
            "avg_wind_speed": sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0,
            "precipitation_sum": precip_sum,
            "precipitation_probability": avg_precip_prob,
            "will_rain": avg_precip_prob > 0.4 or precip_sum > 0.5,
            "avg_cloud_cover": sum(cloud_covers) / len(cloud_covers) if cloud_covers else 50,
            "condition": dominant_condition,
            "condition_ids": weather_ids,
            "raw_periods": periods  # Keep raw data for specialized processing
        }
        
        daily_forecasts.append(day_summary)
    
    return daily_forecasts

def generate_activity_notifications(daily_forecasts: List[Dict[str, Any]], days_ahead: int) -> List[Dict[str, Any]]:
    """
    Generate notifications recommending activities based on suitable weather patterns
    
    Args:
        daily_forecasts (list): Daily forecast summaries
        days_ahead (int): Number of days to look ahead
        
    Returns:
        list: Activity recommendation notifications
    """
    notifications = []
    
    # Ensure we don't look beyond available forecast data
    days_to_check = min(days_ahead, len(daily_forecasts))
    
    # Look for activity-suitable weather patterns
    for activity_type, activity_info in ACTIVITIES.items():
        ideal_conditions = activity_info["ideal_conditions"]
        
        # Find consecutive days matching the activity conditions
        consecutive_days = 0
        start_day_idx = 0
        
        for i in range(days_to_check):
            day = daily_forecasts[i]
            
            conditions_met = True
            
            # Check rain condition if specified
            if "rain" in ideal_conditions:
                if ideal_conditions["rain"] == False and day["will_rain"]:
                    conditions_met = False
                elif ideal_conditions["rain"] == True and not day["will_rain"]:
                    conditions_met = False
            
            # Check temperature range if specified
            if "temp_range" in ideal_conditions:
                min_temp, max_temp = ideal_conditions["temp_range"]
                if day["min_temp"] < min_temp or day["max_temp"] > max_temp:
                    conditions_met = False
            
            # Check humidity range if specified
            if "humidity_range" in ideal_conditions:
                min_humidity, max_humidity = ideal_conditions["humidity_range"]
                if day["min_humidity"] < min_humidity or day["max_humidity"] > max_humidity:
                    conditions_met = False
            
            # Check wind speed if specified
            if "wind_speed_max" in ideal_conditions and day["max_wind_speed"] > ideal_conditions["wind_speed_max"]:
                conditions_met = False
            
            # Check cloud cover if specified
            if "cloud_cover_max" in ideal_conditions and day["avg_cloud_cover"] > ideal_conditions["cloud_cover_max"]:
                conditions_met = False
            
            # Handle consecutive days counting
            if conditions_met:
                if consecutive_days == 0:
                    start_day_idx = i
                consecutive_days += 1
            else:
                # Reset counter if a day doesn't meet conditions
                consecutive_days = 0
            
            # Generate notification if we have enough consecutive good days
            # Most activities need at least 2-3 good days to be noteworthy
            min_days_needed = 3
            
            # Special case for stargazing which counts nights not days
            if activity_type == "stargazing":
                min_days_needed = 2
                
            if consecutive_days >= min_days_needed:
                # Select a random notification template
                notification_templates = activity_info["notifications"]
                template = random.choice(notification_templates)
                
                # Format the notification
                start_date = datetime.strptime(daily_forecasts[start_day_idx]["date"], "%Y-%m-%d").date()
                end_date = start_date + timedelta(days=consecutive_days - 1)
                
                # Special handling for night-only activities
                if "night_only" in activity_info and activity_info["night_only"]:
                    message = template.format(nights=consecutive_days)
                else:
                    message = template.format(days=consecutive_days)
                
                notifications.append({
                    "message": message,
                    "activity_type": activity_type,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "consecutive_days": consecutive_days,
                    "icon": get_activity_icon(activity_type)
                })
                
                # Once we find an activity pattern, break and move to next activity type
                break
    
    return notifications

def generate_warning_notifications(daily_forecasts: List[Dict[str, Any]], days_ahead: int) -> List[Dict[str, Any]]:
    """
    Generate warning notifications based on extreme or noteworthy conditions
    
    Args:
        daily_forecasts (list): Daily forecast summaries
        days_ahead (int): Number of days to look ahead
        
    Returns:
        list: Warning notifications
    """
    notifications = []
    
    # Ensure we don't look beyond available forecast data
    days_to_check = min(days_ahead, len(daily_forecasts))
    
    # Look for weather warning patterns
    for warning_type, warning_info in WEATHER_WARNINGS.items():
        conditions = warning_info["conditions"]
        consecutive_days_needed = conditions.get("consecutive_days", 1)
        
        # Find consecutive days matching the warning conditions
        consecutive_days = 0
        start_day_idx = 0
        
        for i in range(days_to_check):
            day = daily_forecasts[i]
            
            conditions_met = True
            
            # Check temperature minimum if specified
            if "temp_min" in conditions and day["max_temp"] < conditions["temp_min"]:
                conditions_met = False
            
            # Check temperature maximum if specified
            if "temp_max" in conditions and day["min_temp"] > conditions["temp_max"]:
                conditions_met = False
            
            # Check rainfall minimum if specified
            if "rain_min" in conditions and day["precipitation_sum"] < conditions["rain_min"]:
                conditions_met = False
            
            # Check rainfall maximum if specified
            if "rain_max" in conditions and day["precipitation_sum"] > conditions["rain_max"]:
                conditions_met = False
            
            # Check wind speed if specified
            if "wind_min" in conditions and day["max_wind_speed"] < conditions["wind_min"]:
                conditions_met = False
            
            # AQI and UV would require additional data sources, handled separately
            
            # Handle consecutive days counting
            if conditions_met:
                if consecutive_days == 0:
                    start_day_idx = i
                consecutive_days += 1
            else:
                # Reset counter if a day doesn't meet conditions
                consecutive_days = 0
            
            # Generate notification if we have enough consecutive days with warning conditions
            if consecutive_days >= consecutive_days_needed:
                # Select a random notification template
                notification_templates = warning_info["notifications"]
                template = random.choice(notification_templates)
                
                # Format the notification
                start_date = datetime.strptime(daily_forecasts[start_day_idx]["date"], "%Y-%m-%d").date()
                end_date = start_date + timedelta(days=consecutive_days - 1)
                
                # Set variables for template formatting
                format_vars = {
                    "days": consecutive_days
                }
                
                # Add specific condition values based on warning type
                if warning_type == "heat_wave":
                    format_vars["temp"] = conditions["temp_min"]
                elif warning_type == "cold_snap":
                    format_vars["temp"] = conditions["temp_max"]
                elif warning_type == "dry_spell":
                    format_vars["rain"] = conditions["rain_max"]
                elif warning_type == "heavy_rain":
                    format_vars["rain"] = conditions["rain_min"]
                elif warning_type == "high_wind":
                    format_vars["wind"] = conditions["wind_min"]
                elif warning_type == "air_quality":
                    format_vars["aqi"] = conditions["aqi_min"]
                elif warning_type == "high_uv":
                    format_vars["uv"] = conditions["uv_index_min"]
                
                message = template.format(**format_vars)
                
                notifications.append({
                    "message": message,
                    "warning_type": warning_type,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "consecutive_days": consecutive_days,
                    "icon": get_warning_icon(warning_type)
                })
                
                # Once we find a warning pattern, break and move to next warning type
                break
    
    return notifications

def generate_seasonal_notifications(daily_forecasts: List[Dict[str, Any]], city: str) -> List[Dict[str, Any]]:
    """
    Generate seasonal and calendar-aware notifications
    
    Args:
        daily_forecasts (list): Daily forecast summaries
        city (str): City name for location-specific events
        
    Returns:
        list: Seasonal notifications
    """
    notifications = []
    
    # Get current date and look ahead up to 7 days
    today = datetime.now().date()
    
    # Check for upcoming seasonal events
    for day_offset in range(1, 8):  # Look ahead 1-7 days
        check_date = today + timedelta(days=day_offset)
        month_day = (check_date.month, check_date.day)
        
        # Check if date matches any seasonal event
        if month_day in SEASONAL_EVENTS:
            event_name, notification_templates = SEASONAL_EVENTS[month_day]
            template = random.choice(notification_templates)
            
            # Get weather condition for the event day (if we have forecast data)
            condition = "varied"
            for day in daily_forecasts:
                if day["date"] == check_date.strftime("%Y-%m-%d"):
                    condition = day["condition"].lower()
                    break
            
            # Format the notification
            message = template.format(condition=condition)
            
            notifications.append({
                "message": message,
                "event_name": event_name,
                "event_date": check_date.strftime("%Y-%m-%d"),
                "days_away": day_offset,
                "icon": get_seasonal_icon(event_name)
            })
    
    # Check for local weather patterns that align with seasonal transitions
    if len(daily_forecasts) >= 5:
        # Look for temperature trends indicating seasonal shifts
        first_temps = [daily_forecasts[0]["min_temp"], daily_forecasts[0]["max_temp"]]
        last_temps = [daily_forecasts[4]["min_temp"], daily_forecasts[4]["max_temp"]]
        
        temp_change = (sum(last_temps) / 2) - (sum(first_temps) / 2)
        
        # Significant warming or cooling trend
        if abs(temp_change) > 5:
            if temp_change > 0:
                notifications.append({
                    "message": f"Warming trend detected: Temperatures increasing by {temp_change:.1f}°C over the next 5 days.",
                    "trend_type": "warming",
                    "temperature_change": temp_change,
                    "icon": "temperature-arrow-up"
                })
            else:
                notifications.append({
                    "message": f"Cooling trend detected: Temperatures decreasing by {abs(temp_change):.1f}°C over the next 5 days.",
                    "trend_type": "cooling",
                    "temperature_change": temp_change,
                    "icon": "temperature-arrow-down"
                })
    
    return notifications

def generate_weather_pattern_notifications(daily_forecasts: List[Dict[str, Any]], current_weather: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate notifications based on weather patterns and changes
    
    Args:
        daily_forecasts (list): Daily forecast summaries
        current_weather (dict): Current weather conditions
        
    Returns:
        list: Weather pattern notifications
    """
    notifications = []
    
    # Ensure we have forecast data
    if not daily_forecasts or len(daily_forecasts) < 2:
        return notifications
    
    # Detect significant weather changes
    if len(daily_forecasts) >= 3:
        today_conditions = daily_forecasts[0]["condition"].lower()
        tomorrow_conditions = daily_forecasts[1]["condition"].lower()
        
        # Weather changing from good to bad
        if (today_conditions in ["clear", "clouds", "few clouds"] and 
            tomorrow_conditions in ["rain", "thunderstorm", "snow", "drizzle"]):
            notifications.append({
                "message": f"Weather change alert: {today_conditions.capitalize()} today turning to {tomorrow_conditions} tomorrow.",
                "change_type": "deteriorating",
                "icon": "weather-change-down"
            })
        
        # Weather changing from bad to good
        elif (today_conditions in ["rain", "thunderstorm", "snow", "drizzle"] and 
              tomorrow_conditions in ["clear", "clouds", "few clouds"]):
            notifications.append({
                "message": f"Weather improvement ahead: {today_conditions.capitalize()} today clearing to {tomorrow_conditions} tomorrow.",
                "change_type": "improving",
                "icon": "weather-change-up"
            })
    
    # Detect unusual or rare weather patterns
    unusual_patterns = detect_unusual_patterns(daily_forecasts)
    if unusual_patterns:
        notifications.extend(unusual_patterns)
    
    # Weekend weather outlook (if forecast includes weekend days)
    weekend_forecast = get_weekend_forecast(daily_forecasts)
    if weekend_forecast:
        notifications.append(weekend_forecast)
    
    return notifications

def generate_agricultural_notifications(city: str, daily_forecasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate agricultural notifications for gardening and farming
    
    Args:
        city (str): City name
        daily_forecasts (list): Daily forecast summaries
        
    Returns:
        list: Agricultural notifications
    """
    notifications = []
    
    # Ensure we have forecast data
    if not daily_forecasts:
        return notifications
    
    try:
        # Get watering recommendations from agriculture utils
        watering_data = agriculture_utils.get_watering_recommendations(city)
        
        # Check if we have valid watering data
        if watering_data and "watering_recommendation" in watering_data:
            watering_rec = watering_data["watering_recommendation"]
            best_time = watering_data.get("best_watering_time", {})
            
            # Generate notification based on watering recommendation
            if watering_rec.get("should_water", False):
                # Watering is recommended
                water_time = best_time.get("time", "evening")
                water_day = best_time.get("day", "today")
                
                message = f"Garden watering alert: Best time to water is {water_time} {water_day}."
                
                # Add ET information if available
                if "evapotranspiration" in watering_data:
                    et_data = watering_data["evapotranspiration"]
                    et_rating = et_data.get("rating", "moderate")
                    
                    if et_rating in ["high", "very_high"]:
                        message += f" High evapotranspiration expected - plants will lose moisture quickly."
                
                notifications.append({
                    "message": message,
                    "notification_type": "watering",
                    "icon": "water-droplet"
                })
            else:
                # Watering not needed
                if "upcoming_precipitation" in watering_data and watering_data["upcoming_precipitation"].get("expected", False):
                    # Rain expected
                    rain_info = watering_data["upcoming_precipitation"]
                    notifications.append({
                        "message": f"Garden watering notice: Skip watering as rain is expected {rain_info.get('timeframe', 'soon')}.",
                        "notification_type": "watering_skip",
                        "icon": "umbrella-rain"
                    })
        
        # Check for frost risk based on temperatures
        if daily_forecasts and daily_forecasts[0]["min_temp"] < 3:
            notifications.append({
                "message": "Frost alert: Protect sensitive plants tonight as temperatures approach freezing.",
                "notification_type": "frost",
                "icon": "snowflake"
            })
        
        # Check for extreme heat risk for plants
        if daily_forecasts and daily_forecasts[0]["max_temp"] > 32:
            notifications.append({
                "message": "Heat stress alert: Provide afternoon shade and extra water for garden plants today.",
                "notification_type": "heat",
                "icon": "thermometer-hot"
            })
    
    except Exception as e:
        logger.error(f"Error generating agricultural notifications: {e}")
    
    return notifications

def detect_unusual_patterns(daily_forecasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect unusual or rare weather patterns
    
    Args:
        daily_forecasts (list): Daily forecast summaries
        
    Returns:
        list: Unusual pattern notifications
    """
    notifications = []
    
    # Check for rare or unusual patterns
    consecutive_rain_days = 0
    consecutive_clear_days = 0
    
    for day in daily_forecasts:
        condition = day["condition"].lower()
        
        # Count consecutive rain days
        if condition in ["rain", "thunderstorm", "drizzle"]:
            consecutive_rain_days += 1
            consecutive_clear_days = 0
        # Count consecutive clear days
        elif condition in ["clear", "few clouds"]:
            consecutive_clear_days += 1
            consecutive_rain_days = 0
        else:
            # Reset both counters for other conditions
            consecutive_rain_days = 0
            consecutive_clear_days = 0
        
        # Check thresholds for unusual patterns
        if consecutive_rain_days == 4:  # 4+ days of rain is unusual in many climates
            notifications.append({
                "message": f"Unusual pattern: {consecutive_rain_days} consecutive days of rain in the forecast.",
                "pattern_type": "persistent_rain",
                "days": consecutive_rain_days,
                "icon": "cloud-rain-persistent"
            })
            break  # Only report once
            
        if consecutive_clear_days == 5:  # 5+ days of clear weather can be noteworthy
            notifications.append({
                "message": f"Extended clear spell: {consecutive_clear_days} consecutive days of clear skies ahead.",
                "pattern_type": "persistent_clear",
                "days": consecutive_clear_days,
                "icon": "sun-persistent"
            })
            break  # Only report once
    
    # Check for temperature inversions or other unusual temperature patterns
    for i in range(len(daily_forecasts) - 1):
        today = daily_forecasts[i]
        tomorrow = daily_forecasts[i+1]
        
        # Significant temperature drop (>8°C drop in max temperature)
        if tomorrow["max_temp"] < today["max_temp"] - 8:
            notifications.append({
                "message": f"Temperature drop alert: {int(today['max_temp'] - tomorrow['max_temp'])}°C cooler tomorrow compared to today.",
                "pattern_type": "temp_drop",
                "drop_amount": today["max_temp"] - tomorrow["max_temp"],
                "icon": "temperature-drop"
            })
            break  # Only report the first occurrence
        
        # Significant temperature rise (>8°C rise in max temperature)
        if tomorrow["max_temp"] > today["max_temp"] + 8:
            notifications.append({
                "message": f"Temperature surge alert: {int(tomorrow['max_temp'] - today['max_temp'])}°C warmer tomorrow compared to today.",
                "pattern_type": "temp_surge",
                "rise_amount": tomorrow["max_temp"] - today["max_temp"],
                "icon": "temperature-rise"
            })
            break  # Only report the first occurrence
    
    return notifications

def get_weekend_forecast(daily_forecasts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Generate a weekend weather outlook notification
    
    Args:
        daily_forecasts (list): Daily forecast summaries
        
    Returns:
        dict: Weekend forecast notification or None
    """
    # Get today's weekday (0 = Monday, 6 = Sunday)
    today_weekday = datetime.now().weekday()
    
    # Determine days until weekend
    days_to_saturday = (5 - today_weekday) % 7
    days_to_sunday = (6 - today_weekday) % 7
    
    # Check if weekend is within our forecast range
    if days_to_sunday >= len(daily_forecasts):
        return None
    
    # Get weekend days data
    weekend_days = []
    
    if days_to_saturday < len(daily_forecasts):
        weekend_days.append(daily_forecasts[days_to_saturday])
    
    if days_to_sunday < len(daily_forecasts):
        weekend_days.append(daily_forecasts[days_to_sunday])
    
    if not weekend_days:
        return None
    
    # Determine overall weekend weather
    will_rain_weekend = any(day["will_rain"] for day in weekend_days)
    avg_temp = sum(day["avg_temp"] for day in weekend_days) / len(weekend_days)
    
    # Categorize the weekend
    if will_rain_weekend:
        if avg_temp < 10:
            message = "Weekend forecast: Cool and wet conditions expected. Indoor activities recommended."
            icon = "weekend-wet-cold"
        else:
            message = "Weekend forecast: Expect some rainfall. Have indoor backup plans ready."
            icon = "weekend-wet"
    else:
        if avg_temp > 25:
            message = "Weekend forecast: Warm and dry conditions perfect for outdoor activities."
            icon = "weekend-sunny-warm"
        elif avg_temp < 10:
            message = "Weekend forecast: Clear but cool conditions. Dress warmly for outdoor plans."
            icon = "weekend-sunny-cold"
        else:
            message = "Weekend forecast: Pleasant conditions ideal for outdoor activities."
            icon = "weekend-sunny"
    
    return {
        "message": message,
        "pattern_type": "weekend_forecast",
        "will_rain": will_rain_weekend,
        "avg_temp": avg_temp,
        "icon": icon
    }

def get_activity_icon(activity_type: str) -> str:
    """Get appropriate icon for activity notification"""
    icons = {
        "outdoor_painting": "paint-brush",
        "gardening": "leaf",
        "hiking": "hiking",
        "beach_day": "umbrella-beach",
        "laundry_drying": "tshirt",
        "cycling": "bicycle",
        "stargazing": "stars",
        "marathon_training": "running"
    }
    return icons.get(activity_type, "calendar-check")

def get_warning_icon(warning_type: str) -> str:
    """Get appropriate icon for warning notification"""
    icons = {
        "heat_wave": "temperature-high",
        "cold_snap": "temperature-low",
        "dry_spell": "drought",
        "heavy_rain": "cloud-showers-heavy",
        "high_wind": "wind",
        "air_quality": "smog",
        "high_uv": "sun"
    }
    return icons.get(warning_type, "exclamation-triangle")

def get_seasonal_icon(event_name: str) -> str:
    """Get appropriate icon for seasonal notification"""
    if event_name is None:
        return "calendar-day"
        
    icons = {
        "Spring Equinox": "seedling",
        "Summer Solstice": "sun",
        "Fall Equinox": "leaf",
        "Winter Solstice": "snowflake",
        "Earth Day": "globe-americas"
    }
    return icons.get(event_name, "calendar-day")

def get_user_preferences(user_id: str = None) -> Dict[str, Any]:
    """
    Get user preferences for notification types
    Placeholder for integration with user accounts system
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: User preferences
    """
    # This would typically fetch from a database
    # For now, return default preferences
    return {
        "warning_notifications": True,
        "activity_notifications": True,
        "seasonal_notifications": True,
        "agricultural_notifications": True,
        "weather_pattern_notifications": True,
        "max_daily_notifications": 5,
        "preferred_activities": [
            "gardening",
            "outdoor_painting",
            "hiking",
            "cycling"
        ],
        "preferred_locations": []
    }

def filter_by_user_preferences(notifications: List[Dict[str, Any]], user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter notifications based on user preferences
    
    Args:
        notifications (list): List of all generated notifications
        user_preferences (dict): User preferences
        
    Returns:
        list: Filtered notifications
    """
    filtered = []
    
    for notification in notifications:
        notification_type = notification.get("type")
        
        # Check if notification type is enabled
        if notification_type == "warning" and not user_preferences.get("warning_notifications", True):
            continue
        elif notification_type == "activity" and not user_preferences.get("activity_notifications", True):
            continue
        elif notification_type == "seasonal" and not user_preferences.get("seasonal_notifications", True):
            continue
        elif notification_type == "agricultural" and not user_preferences.get("agricultural_notifications", True):
            continue
        elif notification_type == "pattern" and not user_preferences.get("weather_pattern_notifications", True):
            continue
        
        # Check for activity preferences
        if notification_type == "activity":
            activity_type = notification.get("activity_type")
            preferred_activities = user_preferences.get("preferred_activities", [])
            
            if preferred_activities and activity_type not in preferred_activities:
                continue
        
        filtered.append(notification)
    
    # Limit to max notifications
    max_notifications = user_preferences.get("max_daily_notifications", 5)
    return filtered[:max_notifications]