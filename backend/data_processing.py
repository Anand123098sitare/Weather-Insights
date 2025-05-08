import os
import logging
import json
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_marker_data():
    """Process marker data from the AQI and Lat Long CSV file"""
    try:
        # Path to the CSV file
        csv_file_path = 'frontend/static/data/AQI and Lat Long of Countries.csv'
        
        # Check if file exists
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found at {csv_file_path}")
            return []
            
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Process each row into marker data
        markers = []
        for _, row in df.iterrows():
            marker = {
                'City': row['City'],
                'Country': row['Country'],
                'AQI': row['AQI Value'],
                'AQI_Category': row['AQI Category'],
                'Latitude': row['lat'],
                'Longitude': row['lng'],
                'Continent': get_continent_for_country(row['Country'])
            }
            markers.append(marker)
            
        # Save to JSON file
        with open('frontend/static/data/marker_data.json', 'w') as f:
            json.dump(markers, f)
            
        logger.info(f"Processed {len(markers)} markers from CSV file")
        return markers
    except Exception as e:
        logger.error(f"Error processing marker data: {e}")
        return []

def process_countries_data():
    """Process countries data from the world most polluted countries CSV file"""
    try:
        # Path to the CSV file
        csv_file_path = 'frontend/static/data/world_most_polluted_countries_2024.csv'
        
        # Check if file exists
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found at {csv_file_path}")
            return []
            
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Process each row into country data
        countries_data = []
        for _, row in df.iterrows():
            country_data = {
                'Country': row['Country'],
                'Rank': row['Rank'],
                '2024 Avg': row['2024 Avg'],
                'Jan': row['Jan'],
                'Feb': row['Feb'],
                'Mar': row['Mar'],
                'Apr': row['Apr'],
                'May': row['May'],
                'Jun': row['Jun'],
                'Jul': row['Jul'],
                'Aug': row['Aug'],
                'Sep': row['Sep'],
                'Oct': row['Oct'],
                'Nov': row['Nov'],
                'Dec': row['Dec']
            }
            countries_data.append(country_data)
            
        # Save to JSON file
        with open('frontend/static/data/countries_data.json', 'w') as f:
            json.dump(countries_data, f)
            
        logger.info(f"Processed {len(countries_data)} countries from CSV file")
        return countries_data
    except Exception as e:
        logger.error(f"Error processing countries data: {e}")
        return []

def process_cities_monthly_data():
    """Process cities monthly data from the updated polluted cities monthly CSV file"""
    try:
        # Path to the CSV file
        csv_file_path = 'frontend/static/data/updated_polluted_cities_monthly_with_states.csv'
        
        # Check if file exists
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found at {csv_file_path}")
            return []
            
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        # Process each row into city data
        cities_data = []
        for _, row in df.iterrows():
            city_data = {
                'City': row['City'],
                'State': row['State'],
                'Country': row['Country'],
                'Jan': row['Jan'],
                'Feb': row['Feb'],
                'Mar': row['Mar'],
                'Apr': row['Apr'],
                'May': row['May'],
                'Jun': row['Jun'],
                'Jul': row['Jul'],
                'Aug': row['Aug'],
                'Sep': row['Sep'],
                'Oct': row['Oct'],
                'Nov': row['Nov'],
                'Dec': row['Dec']
            }
            cities_data.append(city_data)
            
        # Save to JSON file
        with open('frontend/static/data/cities_monthly_data.json', 'w') as f:
            json.dump(cities_data, f)
            
        logger.info(f"Processed {len(cities_data)} cities from CSV file")
        return cities_data
    except Exception as e:
        logger.error(f"Error processing cities monthly data: {e}")
        return []

def get_continent_for_country(country):
    """Assign continent based on country name"""
    # Define country-to-continent mapping
    country_to_continent = {
        # Asia
        'China': 'Asia',
        'India': 'Asia',
        'Japan': 'Asia',
        'South Korea': 'Asia',
        'Taiwan': 'Asia',
        'Thailand': 'Asia',
        'Vietnam': 'Asia',
        'Indonesia': 'Asia',
        'Malaysia': 'Asia',
        'Singapore': 'Asia',
        'Philippines': 'Asia',
        'Bangladesh': 'Asia',
        'Pakistan': 'Asia',
        'Nepal': 'Asia',
        'Mongolia': 'Asia',
        'Sri Lanka': 'Asia',
        'Myanmar': 'Asia',
        'Kazakhstan': 'Asia',
        'Uzbekistan': 'Asia',
        'Afghanistan': 'Asia',
        'Cambodia': 'Asia',
        'Laos': 'Asia',
        'Hong Kong': 'Asia',
        'Macau': 'Asia',
        
        # North America
        'United States': 'North America',
        'Canada': 'North America',
        'Mexico': 'North America',
        'Cuba': 'North America',
        'Jamaica': 'North America',
        'Puerto Rico': 'North America',
        'Costa Rica': 'North America',
        'Panama': 'North America',
        'Dominican Republic': 'North America',
        'Haiti': 'North America',
        'Guatemala': 'North America',
        'El Salvador': 'North America',
        'Honduras': 'North America',
        'Nicaragua': 'North America',
        
        # South America
        'Brazil': 'South America',
        'Argentina': 'South America',
        'Chile': 'South America',
        'Colombia': 'South America',
        'Peru': 'South America',
        'Venezuela': 'South America',
        'Ecuador': 'South America',
        'Bolivia': 'South America',
        'Uruguay': 'South America',
        'Paraguay': 'South America',
        'Guyana': 'South America',
        'Suriname': 'South America',
        
        # Europe
        'United Kingdom': 'Europe',
        'France': 'Europe',
        'Germany': 'Europe',
        'Italy': 'Europe',
        'Spain': 'Europe',
        'Portugal': 'Europe',
        'Netherlands': 'Europe',
        'Belgium': 'Europe',
        'Switzerland': 'Europe',
        'Austria': 'Europe',
        'Sweden': 'Europe',
        'Norway': 'Europe',
        'Denmark': 'Europe',
        'Finland': 'Europe',
        'Ireland': 'Europe',
        'Greece': 'Europe',
        'Poland': 'Europe',
        'Czech Republic': 'Europe',
        'Hungary': 'Europe',
        'Romania': 'Europe',
        'Bulgaria': 'Europe',
        'Serbia': 'Europe',
        'Croatia': 'Europe',
        'Ukraine': 'Europe',
        'Russia': 'Europe',
        'Turkey': 'Europe',
        
        # Africa
        'South Africa': 'Africa',
        'Nigeria': 'Africa',
        'Egypt': 'Africa',
        'Kenya': 'Africa',
        'Morocco': 'Africa',
        'Ghana': 'Africa',
        'Tanzania': 'Africa',
        'Algeria': 'Africa',
        'Ethiopia': 'Africa',
        'Uganda': 'Africa',
        'Cameroon': 'Africa',
        'Ivory Coast': 'Africa',
        'Senegal': 'Africa',
        'Tunisia': 'Africa',
        
        # Oceania
        'Australia': 'Oceania',
        'New Zealand': 'Oceania',
        'Fiji': 'Oceania',
        'Papua New Guinea': 'Oceania',
        'Solomon Islands': 'Oceania',
    }
    
    # Try to get the continent, default to 'Unknown' if not found
    return country_to_continent.get(country, 'Unknown')

def process_initial_data():
    """Process all initial data from the attached files"""
    try:
        # Create necessary directories
        os.makedirs('frontend/static/data/cache', exist_ok=True)
        
        # Process marker data
        marker_data = process_marker_data()
        
        # Process countries data
        countries_data = process_countries_data()
        
        # Process cities monthly data
        cities_data = process_cities_monthly_data()
        
        logger.info(f"Successfully processed all initial data: {len(marker_data)} markers, {len(countries_data)} countries, {len(cities_data)} cities")
        return True
    except Exception as e:
        logger.error(f"Error processing initial data: {e}")
        return False