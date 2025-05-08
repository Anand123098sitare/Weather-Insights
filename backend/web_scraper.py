"""
Web scraper module for extracting clean text content from websites.
Used for collecting air quality information from various sources.
"""
import re
import logging
try:
    import trafilatura
except ImportError:
    logging.error("Trafilatura package is not installed. Web scraper functionality will not work.")

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    Extract clean text content from a website URL.
    
    This function takes a URL and returns the main text content of the website.
    The text content is extracted using trafilatura and provides cleaner, more
    readable content than raw HTML.
    
    Args:
        url (str): The URL of the website to scrape
        
    Returns:
        str: The extracted text content or error message
    """
    try:
        # Try to import trafilatura
        if 'trafilatura' not in globals():
            return "Error: Trafilatura package is not installed. Please install it to use this feature."
        
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            return f"Error: Could not download content from {url}. The URL might be invalid or the server is not responding."
        
        # Extract text content
        text = trafilatura.extract(downloaded)
        
        if not text:
            return f"Error: Could not extract text content from {url}. The content might be protected or in an unsupported format."
        
        return text
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return f"Error: Failed to extract content from {url}. {str(e)}"

def get_aqi_info_from_url(url: str) -> dict:
    """
    Extract air quality information from a website and format it.
    
    This function extracts text content from a website and attempts to
    identify air quality related information.
    
    Args:
        url (str): The URL of the website with air quality information
        
    Returns:
        dict: Dictionary containing extracted AQI information
    """
    result = {
        "status": "success",
        "url": url,
        "content_extracted": False,
        "aqi_information": {}
    }
    
    try:
        # Get content
        content = get_website_text_content(url)
        
        if content.startswith("Error:"):
            result["status"] = "error"
            result["message"] = content
            return result
        
        # Content successfully extracted
        result["content_extracted"] = True
        
        # Look for AQI information in the text
        # AQI value pattern: digits followed by "AQI" or "air quality index"
        aqi_values = re.findall(r'(\d+)\s*(AQI|air quality index)', content, re.IGNORECASE)
        
        # PM2.5 pattern: digits followed by "µg/m³" or "micrograms per cubic meter" possibly with PM2.5 before or after
        pm25_values = re.findall(r'(PM2\.5.*?(\d+\.?\d*)\s*(µg/m³|micrograms per cubic meter))|(\d+\.?\d*)\s*(µg/m³|micrograms per cubic meter).*?PM2\.5', content, re.IGNORECASE)
        
        # Find city names that might be associated with AQI
        city_pattern = re.compile(r'(air quality|pollution|aqi).{1,30}(in|of|for) ([A-Z][a-z]+ ?[A-Za-z]*)', re.IGNORECASE)
        cities = city_pattern.findall(content)
        
        # Extract AQI categories
        categories = re.findall(r'(good|moderate|unhealthy|hazardous|very unhealthy|unhealthy for sensitive groups) air quality', content, re.IGNORECASE)
        
        # Find pollution sources mentioned
        pollution_sources = re.findall(r'(pollution|pollutant).{1,20}(from|caused by) ([a-z]+ ?[a-z]*)', content, re.IGNORECASE)
        
        # Find health effects
        health_effects = re.findall(r'(health effects|health impacts|symptoms).{1,50}(include|such as|:) ([^.]*)', content, re.IGNORECASE)
        
        # Check if key pollutants are mentioned
        key_pollutants = []
        pollutants = ["PM2.5", "PM10", "ozone", "O3", "NO2", "SO2", "CO"]
        for pollutant in pollutants:
            if re.search(r'\b' + re.escape(pollutant) + r'\b', content, re.IGNORECASE):
                key_pollutants.append(pollutant)
        
        # Check if dates are mentioned (could indicate when the data was measured)
        dates = re.findall(r'\b(\d{1,2} [A-Za-z]{3,9},? \d{4})\b', content)
        
        # Compile results
        result["aqi_information"] = {
            "aqi_values": [v[0] for v in aqi_values] if aqi_values else [],
            "pm25_values": [v[1] for v in pm25_values if len(v) >= 2 and v[1]] if pm25_values else [],
            "cities": [v[2] for v in cities] if cities else [],
            "categories": categories,
            "pollution_sources": [v[2] for v in pollution_sources] if pollution_sources else [],
            "health_effects": [v[2] for v in health_effects] if health_effects else [],
            "key_pollutants": key_pollutants,
            "dates": dates,
            "content_sample": content[:300] + "..." if len(content) > 300 else content
        }
        
        return result
    except Exception as e:
        logger.error(f"Error extracting AQI info from {url}: {e}")
        return {
            "status": "error",
            "message": f"Failed to extract AQI information: {str(e)}",
            "url": url
        }

def get_air_quality_updates() -> list:
    """
    Get air quality updates from multiple predefined sources.
    
    Returns:
        list: List of dictionaries with air quality information from various sources
    """
    sources = [
        {"url": "https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health", "source": "WHO"},
        {"url": "https://www.epa.gov/air-trends/air-quality-national-summary", "source": "EPA"},
        {"url": "https://www.unep.org/explore-topics/air", "source": "UNEP"},
        {"url": "https://www.airnow.gov/", "source": "AirNow"}
    ]
    
    results = []
    
    for source in sources:
        try:
            content = get_website_text_content(source["url"])
            
            result = {
                "source": source["source"],
                "url": source["url"]
            }
            
            if content.startswith("Error:"):
                result["status"] = "error"
                result["message"] = content
            else:
                result["status"] = "success"
                result["content_length"] = len(content)
                result["content_sample"] = content[:300] + "..." if len(content) > 300 else content
            
            results.append(result)
        except Exception as e:
            logger.error(f"Error getting updates from {source['source']}: {e}")
            results.append({
                "source": source["source"],
                "url": source["url"],
                "status": "error",
                "message": str(e)
            })
    
    return results