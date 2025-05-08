"""
Utilities for travel and commute forecasts based on weather conditions
"""
import os
import json
import random
import logging
import datetime
from typing import Dict, List, Optional, Union, Any

from backend import api_utils, health_utils, weather_utils

logger = logging.getLogger(__name__)

def get_commute_impact(city: str, start_time: str, end_time: str, route_type: str = "drive", 
                       normal_duration: int = 30) -> Dict[str, Any]:
    """
    Get weather impact on commute for a specific city, time, and route type
    
    Args:
        city (str): City name
        start_time (str): Start time in 24-hour format (HH:MM)
        end_time (str): End time in 24-hour format (HH:MM)
        route_type (str): Type of commute (drive, transit, bike, walk)
        normal_duration (int): Normal duration in minutes without weather impact
        
    Returns:
        dict: Commute impact data including delay predictions
    """
    try:
        # Get current weather and forecast
        current_weather = weather_utils.get_city_weather(city)
        forecast = weather_utils.get_weather_forecast(city)
        
        # Get time ranges for commute
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        
        # Extract relevant forecast for commute time
        commute_weather = []
        
        if forecast and 'list' in forecast:
            for period in forecast['list']:
                forecast_time = datetime.datetime.fromtimestamp(period['dt'])
                forecast_hour = forecast_time.hour
                
                # Check if forecast is within commute hours
                if start_hour <= forecast_hour <= end_hour:
                    commute_weather.append(period)
        
        # If no forecast data available, use current weather
        if not commute_weather:
            # Create a simulated forecast for the commute time
            commute_weather = [{
                'dt': datetime.datetime.now().timestamp(),
                'main': current_weather.get('main', {}),
                'weather': current_weather.get('weather', []),
                'clouds': current_weather.get('clouds', {}),
                'wind': current_weather.get('wind', {})
            }]
            
        # Calculate delay factors based on weather conditions
        delay_factors = []
        weather_impacts = []
        total_impact_score = 0
        
        for period in commute_weather:
            # Extract weather conditions
            weather_condition = period.get('weather', [{}])[0].get('main', '').lower()
            weather_description = period.get('weather', [{}])[0].get('description', '').lower()
            wind_speed = period.get('wind', {}).get('speed', 0)
            temperature = period.get('main', {}).get('temp', 20)
            
            # Initialize delay factor and impact
            delay_factor = 0
            impact = ""
            
            # Calculate delay based on weather condition
            if 'thunderstorm' in weather_condition:
                delay_factor = 0.5  # 50% delay
                impact = "Thunderstorm significantly slows traffic"
            elif 'rain' in weather_condition or 'drizzle' in weather_condition:
                if 'heavy' in weather_description or 'extreme' in weather_description:
                    delay_factor = 0.4  # 40% delay
                    impact = "Heavy rain reduces visibility and creates slippery roads"
                else:
                    delay_factor = 0.2  # 20% delay
                    impact = "Light rain may cause slowdowns"
            elif 'snow' in weather_condition:
                if 'heavy' in weather_description:
                    delay_factor = 0.6  # 60% delay
                    impact = "Heavy snow makes roads hazardous"
                else:
                    delay_factor = 0.3  # 30% delay
                    impact = "Light snow may cause slowdowns"
            elif 'fog' in weather_condition or 'mist' in weather_description:
                delay_factor = 0.25  # 25% delay
                impact = "Fog reduces visibility"
            elif 'smoke' in weather_condition or 'haze' in weather_condition:
                delay_factor = 0.15  # 15% delay
                impact = "Reduced visibility from smoke/haze"
            elif 'clear' in weather_condition:
                delay_factor = 0  # No delay
                impact = "Clear conditions, no weather impact"
            else:
                delay_factor = 0.05  # 5% default delay for cloudy
                impact = "Normal traffic flow expected"
                
            # Adjust for wind speed
            if wind_speed > 20:
                delay_factor += 0.15
                impact += " with high winds increasing risk"
            elif wind_speed > 10:
                delay_factor += 0.05
                impact += " with moderate winds"
                
            # Adjust for extreme temperatures
            if temperature < -5:
                delay_factor += 0.1
                impact += ", extreme cold may affect vehicles"
            elif temperature > 35:
                delay_factor += 0.05
                impact += ", extreme heat may affect road conditions"
                
            # Adjust for transportation mode
            if route_type == "bike":
                # Biking is more impacted by weather
                delay_factor *= 1.5
                if wind_speed > 10:
                    delay_factor += 0.2
                    impact += ", headwinds will slow cycling"
            elif route_type == "walk":
                # Walking is even more impacted
                delay_factor *= 2
            elif route_type == "transit":
                # Public transit slightly less impacted than driving
                delay_factor *= 0.8
                
            delay_factors.append(delay_factor)
            weather_impacts.append(impact)
            total_impact_score += delay_factor
            
        # Calculate average delay factor
        avg_delay_factor = sum(delay_factors) / len(delay_factors) if delay_factors else 0
        
        # Calculate total delay in minutes
        delay_minutes = round(normal_duration * avg_delay_factor)
        total_commute_time = normal_duration + delay_minutes
        
        # Determine severity level
        if avg_delay_factor < 0.1:
            severity = "minimal"
            alert_type = "success"
        elif avg_delay_factor < 0.2:
            severity = "minor"
            alert_type = "info"
        elif avg_delay_factor < 0.3:
            severity = "moderate"
            alert_type = "warning"
        else:
            severity = "severe"
            alert_type = "danger"
            
        # Generate summary message
        if delay_minutes == 0:
            summary = f"Good news! No weather-related delays expected for your {route_type} commute ({start_time}–{end_time})."
        else:
            weather_condition = commute_weather[0].get('weather', [{}])[0].get('main', '')
            summary = f"{weather_condition} expected on your {route_type} commute ({start_time}–{end_time}). Allow {delay_minutes} extra minutes."
            
        # Generate recommendations
        recommendations = get_travel_recommendations(route_type, avg_delay_factor, commute_weather)
        
        # Create hour-by-hour breakdown of the commute weather
        hourly_forecast = []
        for period in commute_weather:
            forecast_time = datetime.datetime.fromtimestamp(period['dt'])
            
            hourly_data = {
                "time": forecast_time.strftime("%H:%M"),
                "condition": period.get('weather', [{}])[0].get('main', ''),
                "description": period.get('weather', [{}])[0].get('description', ''),
                "temperature": period.get('main', {}).get('temp', 0),
                "wind_speed": period.get('wind', {}).get('speed', 0),
                "icon": period.get('weather', [{}])[0].get('icon', '01d')
            }
            
            hourly_forecast.append(hourly_data)
            
        return {
            "summary": summary,
            "normal_duration": normal_duration,
            "delay_minutes": delay_minutes,
            "total_duration": total_commute_time,
            "severity": severity,
            "alert_type": alert_type,
            "recommendations": recommendations,
            "hourly_forecast": hourly_forecast,
            "weather_impacts": weather_impacts
        }
        
    except Exception as e:
        logger.error(f"Error getting commute impact for {city}: {e}")
        return {
            "summary": f"Unable to determine accurate travel time for your commute ({start_time}–{end_time}).",
            "normal_duration": normal_duration,
            "delay_minutes": 5,
            "total_duration": normal_duration + 5,
            "severity": "unknown",
            "alert_type": "info",
            "recommendations": [
                "Check local weather conditions before departing",
                "Allow extra time for your commute"
            ],
            "hourly_forecast": [],
            "weather_impacts": []
        }

def get_route_options(city: str, from_location: str, to_location: str, departure_time: str) -> Dict[str, Any]:
    """
    Get weather-optimized route options for a specific journey
    
    Args:
        city (str): City name
        from_location (str): Starting location
        to_location (str): Destination
        departure_time (str): Departure time in 24-hour format (HH:MM)
        
    Returns:
        dict: Route options with weather impact data
    """
    try:
        # Get weather forecast
        forecast = weather_utils.get_weather_forecast(city)
        
        # Parse departure time
        departure_hour = int(departure_time.split(':')[0])
        
        # Find relevant forecast for departure time
        departure_weather = None
        
        if forecast and 'list' in forecast:
            for period in forecast['list']:
                forecast_time = datetime.datetime.fromtimestamp(period['dt'])
                if forecast_time.hour == departure_hour:
                    departure_weather = period
                    break
                    
        # If no specific forecast found, use current weather
        if not departure_weather:
            current_weather = weather_utils.get_city_weather(city)
            departure_weather = {
                'dt': datetime.datetime.now().timestamp(),
                'main': current_weather.get('main', {}),
                'weather': current_weather.get('weather', []),
                'clouds': current_weather.get('clouds', {}),
                'wind': current_weather.get('wind', {})
            }
            
        # Generate route options
        routes = []
        
        # Route 1: Main route
        main_route = {
            "name": "Main Route",
            "description": "Standard route",
            "distance": round(random.uniform(8, 12), 1),  # km
            "duration": random.randint(25, 35),  # minutes
        }
        
        # Calculate weather impact
        main_weather_impact = calculate_route_weather_impact(departure_weather, main_route["duration"])
        main_route.update(main_weather_impact)
        routes.append(main_route)
        
        # Route 2: Alternate route
        alt_route = {
            "name": "Alternate Route",
            "description": "Alternative road network",
            "distance": round(random.uniform(9, 14), 1),  # km
            "duration": random.randint(28, 38),  # minutes
        }
        
        # Calculate weather impact
        alt_weather_impact = calculate_route_weather_impact(departure_weather, alt_route["duration"])
        alt_route.update(alt_weather_impact)
        routes.append(alt_route)
        
        # Route 3: Weather-optimized route
        weather_route = {
            "name": "Weather-optimized Route",
            "description": "Route adjusted for current weather conditions",
            "distance": round(random.uniform(10, 15), 1),  # km
            "duration": random.randint(30, 40),  # minutes
        }
        
        # Make weather route slightly better in bad weather
        weather_condition = departure_weather.get('weather', [{}])[0].get('main', '').lower()
        if 'rain' in weather_condition or 'snow' in weather_condition or 'storm' in weather_condition:
            # Reduce the impact for the weather-optimized route
            weather_route_impact = calculate_route_weather_impact(departure_weather, weather_route["duration"], reduction_factor=0.5)
        else:
            # Normal impact for good weather
            weather_route_impact = calculate_route_weather_impact(departure_weather, weather_route["duration"])
            
        weather_route.update(weather_route_impact)
        routes.append(weather_route)
        
        # Find recommended route (lowest total time)
        recommended_route = min(routes, key=lambda x: x["total_duration"])
        
        return {
            "from": from_location,
            "to": to_location,
            "departure_time": departure_time,
            "routes": routes,
            "recommended_route": recommended_route["name"],
            "weather_condition": departure_weather.get('weather', [{}])[0].get('main', ''),
            "weather_description": departure_weather.get('weather', [{}])[0].get('description', '')
        }
        
    except Exception as e:
        logger.error(f"Error getting route options for {city}: {e}")
        return {
            "from": from_location,
            "to": to_location,
            "departure_time": departure_time,
            "routes": [
                {
                    "name": "Default Route",
                    "description": "Standard route",
                    "distance": 10.0,
                    "duration": 30,
                    "delay_minutes": 5,
                    "total_duration": 35,
                    "weather_impact": "Some delays possible due to weather",
                    "severity": "minor",
                    "alert_type": "info"
                }
            ],
            "recommended_route": "Default Route",
            "weather_condition": "Unknown",
            "weather_description": "Check local forecasts for details"
        }

def calculate_route_weather_impact(weather_data: Dict[str, Any], base_duration: int, reduction_factor: float = 1.0) -> Dict[str, Any]:
    """
    Calculate weather impact on a specific route
    
    Args:
        weather_data (dict): Weather forecast data
        base_duration (int): Base duration of the route in minutes
        reduction_factor (float): Factor to reduce weather impact (for weather-optimized routes)
        
    Returns:
        dict: Weather impact data for the route
    """
    # Extract weather conditions
    weather_condition = weather_data.get('weather', [{}])[0].get('main', '').lower()
    weather_description = weather_data.get('weather', [{}])[0].get('description', '').lower()
    wind_speed = weather_data.get('wind', {}).get('speed', 0)
    
    # Initialize delay factor
    delay_factor = 0
    impact = "Normal traffic flow expected"
    
    # Calculate delay based on weather condition
    if 'thunderstorm' in weather_condition:
        delay_factor = 0.5  # 50% delay
        impact = "Thunderstorm significantly slows traffic"
    elif 'rain' in weather_condition or 'drizzle' in weather_condition:
        if 'heavy' in weather_description or 'extreme' in weather_description:
            delay_factor = 0.4  # 40% delay
            impact = "Heavy rain reduces visibility and creates slippery roads"
        else:
            delay_factor = 0.2  # 20% delay
            impact = "Light rain may cause slowdowns"
    elif 'snow' in weather_condition:
        if 'heavy' in weather_description:
            delay_factor = 0.6  # 60% delay
            impact = "Heavy snow makes roads hazardous"
        else:
            delay_factor = 0.3  # 30% delay
            impact = "Light snow may cause slowdowns"
    elif 'fog' in weather_condition or 'mist' in weather_description:
        delay_factor = 0.25  # 25% delay
        impact = "Fog reduces visibility"
    elif 'smoke' in weather_condition or 'haze' in weather_condition:
        delay_factor = 0.15  # 15% delay
        impact = "Reduced visibility from smoke/haze"
    elif 'clear' in weather_condition:
        delay_factor = 0  # No delay
        impact = "Clear conditions, no weather impact"
    else:
        delay_factor = 0.05  # 5% default delay for cloudy
        impact = "Normal traffic flow expected"
        
    # Adjust for wind speed
    if wind_speed > 20:
        delay_factor += 0.15
        impact += " with high winds increasing risk"
    elif wind_speed > 10:
        delay_factor += 0.05
        impact += " with moderate winds"
    
    # Apply reduction factor for weather-optimized routes
    delay_factor *= reduction_factor
    
    # Calculate delay in minutes
    delay_minutes = round(base_duration * delay_factor)
    total_duration = base_duration + delay_minutes
    
    # Determine severity level
    if delay_factor < 0.1:
        severity = "minimal"
        alert_type = "success"
    elif delay_factor < 0.2:
        severity = "minor"
        alert_type = "info"
    elif delay_factor < 0.3:
        severity = "moderate"
        alert_type = "warning"
    else:
        severity = "severe"
        alert_type = "danger"
        
    return {
        "delay_minutes": delay_minutes,
        "total_duration": total_duration,
        "weather_impact": impact,
        "severity": severity,
        "alert_type": alert_type
    }

def get_travel_recommendations(route_type: str, delay_factor: float, weather_data: List[Dict[str, Any]]) -> List[str]:
    """
    Generate travel recommendations based on weather conditions and route type
    
    Args:
        route_type (str): Type of commute (drive, transit, bike, walk)
        delay_factor (float): Calculated delay factor
        weather_data (list): List of weather forecast data for commute hours
        
    Returns:
        list: List of travel recommendations
    """
    recommendations = []
    
    # Extract worst weather condition during commute
    worst_weather = "clear"
    worst_description = ""
    max_wind = 0
    min_temp = 100
    max_temp = -100
    
    for period in weather_data:
        weather_condition = period.get('weather', [{}])[0].get('main', '').lower()
        weather_description = period.get('weather', [{}])[0].get('description', '').lower()
        wind_speed = period.get('wind', {}).get('speed', 0)
        temp = period.get('main', {}).get('temp', 20)
        
        # Update worst conditions
        condition_severity = {
            "thunderstorm": 5,
            "snow": 4,
            "rain": 3,
            "drizzle": 2,
            "fog": 2,
            "mist": 2,
            "haze": 1,
            "clouds": 0,
            "clear": 0
        }
        
        current_severity = 0
        for cond, severity in condition_severity.items():
            if cond in weather_condition:
                current_severity = severity
                break
                
        worst_severity = 0
        for cond, severity in condition_severity.items():
            if cond in worst_weather:
                worst_severity = severity
                break
                
        if current_severity > worst_severity:
            worst_weather = weather_condition
            worst_description = weather_description
            
        # Update wind and temp extremes
        max_wind = max(max_wind, wind_speed)
        min_temp = min(min_temp, temp)
        max_temp = max(max_temp, temp)
    
    # General recommendations based on delay factor
    if delay_factor >= 0.3:
        recommendations.append("Plan for significant delays and leave earlier than usual")
    elif delay_factor >= 0.15:
        recommendations.append("Allow extra time for your commute")
        
    # Weather-specific recommendations
    if "thunderstorm" in worst_weather:
        recommendations.append("Be cautious of flash flooding and reduced visibility")
        if route_type == "drive":
            recommendations.append("Drive slowly and maintain a safe following distance")
        elif route_type in ["bike", "walk"]:
            recommendations.append("Consider alternative transportation modes during thunderstorms")
    elif "snow" in worst_weather:
        if route_type == "drive":
            recommendations.append("Ensure your vehicle is properly equipped for snow conditions")
            recommendations.append("Drive slowly and avoid sudden maneuvers")
        elif route_type == "bike":
            recommendations.append("Consider public transit instead of biking in snow")
        elif route_type == "walk":
            recommendations.append("Wear appropriate footwear with good traction")
    elif "rain" in worst_weather or "drizzle" in worst_weather:
        if route_type == "drive":
            recommendations.append("Use headlights and reduce speed in rainy conditions")
        elif route_type == "bike":
            recommendations.append("Wear waterproof clothing and use fenders on your bike")
        elif route_type == "walk":
            recommendations.append("Bring an umbrella and wear waterproof footwear")
    elif "fog" in worst_weather or "mist" in worst_description:
        if route_type == "drive":
            recommendations.append("Use low-beam headlights and drive slowly in foggy conditions")
        elif route_type in ["bike", "walk"]:
            recommendations.append("Wear bright or reflective clothing to increase visibility")
            
    # Wind recommendations
    if max_wind > 20:
        if route_type == "drive":
            recommendations.append("Be cautious of strong crosswinds, especially on bridges")
        elif route_type == "bike":
            recommendations.append("Be prepared for difficult cycling conditions due to strong winds")
        
    # Temperature recommendations
    if min_temp < 0:
        if route_type == "drive":
            recommendations.append("Watch for icy patches, especially on bridges and overpasses")
        elif route_type in ["bike", "walk"]:
            recommendations.append("Dress in warm layers and protect exposed skin in cold temperatures")
    elif max_temp > 35:
        if route_type in ["bike", "walk"]:
            recommendations.append("Stay hydrated and take breaks in shade during hot weather travel")
            
    # Route-specific recommendations
    if route_type == "transit":
        recommendations.append("Check transit alerts for weather-related delays or service changes")
    elif route_type == "bike":
        recommendations.append("Check bike paths for weather-related closures or hazards")
    elif route_type == "walk":
        recommendations.append("Use walking paths that are well-maintained during adverse weather")
    
    # If no specific recommendations were added, add a default one
    if not recommendations:
        recommendations.append("Travel conditions look favorable for your commute")
        
    return recommendations

def get_travel_forecast(city: str, routes: List[Dict[str, Any]], days: int = 5) -> Dict[str, Any]:
    """
    Get multi-day travel forecast for a specific city and set of routes
    
    Args:
        city (str): City name
        routes (list): List of routes with locations and normal durations
        days (int): Number of days to forecast
        
    Returns:
        dict: Multi-day travel forecast data
    """
    try:
        # Get weather forecast
        weather_forecast = weather_utils.get_weather_forecast(city)
        
        # Generate daily forecasts
        daily_forecasts = []
        
        # Current date
        current_date = datetime.datetime.now()
        
        for day in range(days):
            forecast_date = current_date + datetime.timedelta(days=day)
            
            # Find weather for this day
            day_weather = []
            
            if weather_forecast and 'list' in weather_forecast:
                for period in weather_forecast['list']:
                    period_date = datetime.datetime.fromtimestamp(period['dt'])
                    if period_date.date() == forecast_date.date():
                        day_weather.append(period)
            
            # If no forecast data available, use simulated weather
            if not day_weather:
                if day == 0:
                    # Use current weather for today
                    current_weather = weather_utils.get_city_weather(city)
                    day_weather = [{
                        'dt': current_date.timestamp(),
                        'main': current_weather.get('main', {}),
                        'weather': current_weather.get('weather', []),
                        'clouds': current_weather.get('clouds', {}),
                        'wind': current_weather.get('wind', {})
                    }]
                else:
                    # Generate simulated weather for future days
                    # This should be replaced with actual forecast data
                    day_weather = [{
                        'dt': forecast_date.timestamp(),
                        'main': {
                            'temp': 20 + random.uniform(-5, 5),
                            'humidity': random.randint(40, 90)
                        },
                        'weather': [{
                            'main': random.choice(['Clear', 'Clouds', 'Rain']),
                            'description': random.choice(['clear sky', 'few clouds', 'light rain'])
                        }],
                        'clouds': {'all': random.randint(0, 100)},
                        'wind': {'speed': random.uniform(2, 10)}
                    }]
            
            # Analyze route impacts for each time of day
            morning_impact = calculate_time_of_day_impact(day_weather, "morning", routes)
            afternoon_impact = calculate_time_of_day_impact(day_weather, "afternoon", routes)
            evening_impact = calculate_time_of_day_impact(day_weather, "evening", routes)
            
            # Determine overall day impact
            impacts = [morning_impact["avg_delay_factor"], afternoon_impact["avg_delay_factor"], evening_impact["avg_delay_factor"]]
            avg_impact = sum(impacts) / len(impacts) if impacts else 0
            
            # Determine overall severity
            if avg_impact < 0.1:
                severity = "minimal"
                alert_type = "success"
            elif avg_impact < 0.2:
                severity = "minor"
                alert_type = "info"
            elif avg_impact < 0.3:
                severity = "moderate"
                alert_type = "warning"
            else:
                severity = "severe"
                alert_type = "danger"
                
            # Generate day summary
            day_weather_condition = day_weather[0].get('weather', [{}])[0].get('main', '') if day_weather else "Unknown"
            
            if avg_impact < 0.1:
                day_summary = f"Good travel conditions expected throughout the day."
            else:
                # Identify worst time of day
                worst_time = "morning"
                if afternoon_impact["avg_delay_factor"] > morning_impact["avg_delay_factor"] and afternoon_impact["avg_delay_factor"] > evening_impact["avg_delay_factor"]:
                    worst_time = "afternoon"
                elif evening_impact["avg_delay_factor"] > morning_impact["avg_delay_factor"] and evening_impact["avg_delay_factor"] > afternoon_impact["avg_delay_factor"]:
                    worst_time = "evening"
                
                if worst_time == "morning":
                    day_summary = f"{day_weather_condition} may impact morning commute. Afternoon and evening travel should be better."
                elif worst_time == "afternoon":
                    day_summary = f"{day_weather_condition} may impact afternoon travel. Morning commute should be better."
                else:
                    day_summary = f"{day_weather_condition} may impact evening commute. Morning travel should be better."
            
            daily_forecasts.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "day_name": forecast_date.strftime("%A"),
                "morning": morning_impact,
                "afternoon": afternoon_impact,
                "evening": evening_impact,
                "avg_impact": avg_impact,
                "severity": severity,
                "alert_type": alert_type,
                "summary": day_summary,
                "weather_condition": day_weather_condition
            })
        
        return {
            "city": city,
            "forecast_days": daily_forecasts,
            "routes": routes,
        }
        
    except Exception as e:
        logger.error(f"Error getting travel forecast for {city}: {e}")
        return {
            "city": city,
            "forecast_days": [],
            "routes": routes,
            "error": str(e)
        }

def calculate_time_of_day_impact(day_weather: List[Dict[str, Any]], time_of_day: str, routes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate weather impact on routes for a specific time of day
    
    Args:
        day_weather (list): List of weather forecast periods for the day
        time_of_day (str): Time of day (morning, afternoon, evening)
        routes (list): List of routes with locations and normal durations
        
    Returns:
        dict: Weather impact data for the specific time of day
    """
    # Define hour ranges for times of day
    hour_ranges = {
        "morning": (6, 10),  # 6 AM - 10 AM
        "afternoon": (11, 16),  # 11 AM - 4 PM
        "evening": (17, 22)  # 5 PM - 10 PM
    }
    
    start_hour, end_hour = hour_ranges.get(time_of_day, (0, 23))
    
    # Find weather periods for this time of day
    time_weather = []
    for period in day_weather:
        period_hour = datetime.datetime.fromtimestamp(period['dt']).hour
        if start_hour <= period_hour <= end_hour:
            time_weather.append(period)
    
    # If no specific weather for this time, use all day weather
    if not time_weather:
        time_weather = day_weather
    
    # Calculate impact for each route
    route_impacts = []
    total_delay_factor = 0
    
    for route in routes:
        # Use the first weather period for simplicity
        weather_period = time_weather[0] if time_weather else day_weather[0] if day_weather else None
        
        if weather_period:
            impact = calculate_route_weather_impact(weather_period, route.get("duration", 30))
            route_impacts.append({
                "route_name": route.get("name", "Route"),
                "normal_duration": route.get("duration", 30),
                "delay_minutes": impact["delay_minutes"],
                "total_duration": impact["total_duration"],
                "weather_impact": impact["weather_impact"],
                "severity": impact["severity"],
                "alert_type": impact["alert_type"]
            })
            
            # Extract delay factor for average calculation
            delay_minutes = impact["delay_minutes"]
            normal_duration = route.get("duration", 30)
            delay_factor = delay_minutes / normal_duration if normal_duration > 0 else 0
            total_delay_factor += delay_factor
        
    # Calculate average delay factor
    avg_delay_factor = total_delay_factor / len(routes) if routes else 0
    
    # Determine time of day severity
    if avg_delay_factor < 0.1:
        severity = "minimal"
        alert_type = "success"
    elif avg_delay_factor < 0.2:
        severity = "minor"
        alert_type = "info"
    elif avg_delay_factor < 0.3:
        severity = "moderate"
        alert_type = "warning"
    else:
        severity = "severe"
        alert_type = "danger"
    
    # Weather condition for this time of day
    weather_condition = time_weather[0].get('weather', [{}])[0].get('main', '') if time_weather else "Unknown"
    
    return {
        "time_of_day": time_of_day,
        "route_impacts": route_impacts,
        "avg_delay_factor": avg_delay_factor,
        "severity": severity,
        "alert_type": alert_type,
        "weather_condition": weather_condition
    }