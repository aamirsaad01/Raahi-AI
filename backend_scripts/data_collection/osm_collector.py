import pandas as pd
import requests
import time
import os
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.distance import geodesic
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define regional boundaries (approximate bounding boxes)
REGION_BOUNDARIES = {
    "Gilgit-Baltistan": {
        "min_lat": 35.0,
        "max_lat": 37.0,
        "min_lon": 72.5,
        "max_lon": 77.0,
        "center": (35.9208, 74.3080)  # Gilgit city
    },
    "KPK Highlands": {
        "min_lat": 34.5,
        "max_lat": 36.9,
        "min_lon": 71.0,
        "max_lon": 73.0,
        "center": (35.5307, 72.3600)  # Chitral
    },
    "Hazara Division": {
        "min_lat": 34.0,
        "max_lat": 35.5,
        "min_lon": 72.8,
        "max_lon": 74.0,
        "center": (34.1688, 73.2215)  # Abbottabad
    },
    "Murree & Galyat": {
        "min_lat": 33.8,
        "max_lat": 34.3,
        "min_lon": 73.2,
        "max_lon": 73.7,
        "center": (33.9070, 73.3943)  # Murree
    }
}

class LocationManager:
    def __init__(self, csv_path='E:/Raahi-AI/backend_scripts/data/location_mapping.csv'):
        self.csv_path = csv_path
        self.geolocator = Nominatim(user_agent="raahi_ai_v2", timeout=10)
        self.locations_df = self._load_or_create_database()
        
    def _load_or_create_database(self):
        """Load existing database or create new one"""
        if os.path.exists(self.csv_path):
            logger.info(f"Loading existing database from {self.csv_path}")
            return pd.read_csv(self.csv_path)
        else:
            logger.info("Creating new database")
            return pd.DataFrame(columns=[
                'city', 'parent_region', 'elevation', 'climate_zone',
                'tourist_season', 'latitude', 'longitude', 'verified'
            ])
    
    def save_database(self):
        """Save current database to CSV"""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        self.locations_df.to_csv(self.csv_path, index=False)
        logger.info(f"Database saved with {len(self.locations_df)} locations")
    
    def is_within_region(self, lat, lon, region_name):
        """Check if coordinates are within region boundaries"""
        if region_name not in REGION_BOUNDARIES:
            return False
        
        bounds = REGION_BOUNDARIES[region_name]
        return (bounds["min_lat"] <= lat <= bounds["max_lat"] and
                bounds["min_lon"] <= lon <= bounds["max_lon"])
    
    def get_elevation(self, lat, lon):
        """Fetch elevation data using Open-Elevation API"""
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()['results'][0]['elevation']
            return None
        except Exception as e:
            logger.error(f"Error getting elevation: {str(e)}")
            return None
    
    def get_coordinates(self, city_name, region_name=None):
        """Get coordinates using Nominatim with region context"""
        try:
            # Try with region first for better accuracy
            if region_name:
                search_query = f"{city_name}, {region_name}, Pakistan"
            else:
                search_query = f"{city_name}, Northern Pakistan"
            
            location = self.geolocator.geocode(search_query)
            
            # Fallback: try without region
            if not location:
                location = self.geolocator.geocode(f"{city_name}, Pakistan")
            
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            logger.error(f"Error geocoding {city_name}: {str(e)}")
            return None, None
    
    def get_climate_zone(self, elevation):
        """Determine climate zone based on elevation"""
        if elevation is None:
            return "unknown"
        if elevation > 2500:
            return "alpine"
        elif elevation > 1500:
            return "temperate"
        elif elevation > 1000:
            return "subtropical"
        return "warm"
    
    def get_tourist_season(self, climate_zone):
        """Determine prime tourist season based on climate zone"""
        seasons = {
            "alpine": "June-September",
            "temperate": "March-October",
            "subtropical": "March-November",
            "warm": "October-March",
            "unknown": "All year"
        }
        return seasons.get(climate_zone, "All year")
    
    def find_closest_region(self, lat, lon):
        """Find the closest region to given coordinates"""
        min_distance = float('inf')
        closest_region = None
        
        for region_name, bounds in REGION_BOUNDARIES.items():
            center = bounds["center"]
            distance = geodesic((lat, lon), center).kilometers
            if distance < min_distance:
                min_distance = distance
                closest_region = region_name
        
        return closest_region, min_distance
    
    def lookup_location(self, area_name, region_name=None):
        """
        Lookup location with dynamic fallback
        
        Returns: dict with location data or None
        """
        # Step 1: Check if location exists in database
        query = self.locations_df['city'].str.lower() == area_name.lower()
        if region_name:
            query = query & (self.locations_df['parent_region'] == region_name)
        
        existing = self.locations_df[query]
        
        if not existing.empty:
            logger.info(f"Found {area_name} in database")
            return existing.iloc[0].to_dict()
        
        # Step 2: Dynamic lookup via geocoding
        logger.info(f"Location not in database. Attempting dynamic lookup for: {area_name}")
        lat, lon = self.get_coordinates(area_name, region_name)
        
        if lat is None or lon is None:
            logger.warning(f"Could not geocode {area_name}")
            return None
        
        # Step 3: Verify region if specified
        if region_name:
            if not self.is_within_region(lat, lon, region_name):
                logger.warning(f"{area_name} coordinates are outside {region_name} boundaries")
                # Find actual region
                actual_region, distance = self.find_closest_region(lat, lon)
                logger.info(f"Location appears to be in {actual_region} (distance: {distance:.1f}km)")
                
                # Ask user or use closest region
                region_name = actual_region
        else:
            # Determine region from coordinates
            region_name, _ = self.find_closest_region(lat, lon)
        
        # Step 4: Get elevation and other details
        elevation = self.get_elevation(lat, lon)
        climate = self.get_climate_zone(elevation)
        
        location_data = {
            'city': area_name,
            'parent_region': region_name,
            'elevation': elevation,
            'climate_zone': climate,
            'tourist_season': self.get_tourist_season(climate),
            'latitude': lat,
            'longitude': lon,
            'verified': False  # Mark as unverified since it's dynamic
        }
        
        # Step 5: Add to database for future use
        self.locations_df = pd.concat([
            self.locations_df,
            pd.DataFrame([location_data])
        ], ignore_index=True)
        
        logger.info(f"Added new location: {area_name} in {region_name}")
        return location_data
    
    def batch_add_curated_locations(self, locations_dict):
        """Add multiple curated locations from predefined list"""
        added_count = 0
        
        for region, cities in locations_dict.items():
            logger.info(f"Processing region: {region}")
            
            for city in cities:
                # Check if already exists
                if not self.locations_df[
                    self.locations_df['city'].str.lower() == city.lower()
                ].empty:
                    logger.info(f"{city} already in database, skipping")
                    continue
                
                try:
                    logger.info(f"Processing {city}...")
                    
                    lat, lon = self.get_coordinates(city, region)
                    if lat is None or lon is None:
                        logger.warning(f"Could not find coordinates for {city}")
                        continue
                    
                    elevation = self.get_elevation(lat, lon)
                    climate = self.get_climate_zone(elevation)
                    
                    location = {
                        'city': city,
                        'parent_region': region,
                        'elevation': elevation,
                        'climate_zone': climate,
                        'tourist_season': self.get_tourist_season(climate),
                        'latitude': lat,
                        'longitude': lon,
                        'verified': True  # Curated locations are verified
                    }
                    
                    self.locations_df = pd.concat([
                        self.locations_df,
                        pd.DataFrame([location])
                    ], ignore_index=True)
                    
                    added_count += 1
                    logger.info(f"Added {city} to database")
                    
                    time.sleep(1.5)  # Respect API rate limits
                    
                except Exception as e:
                    logger.error(f"Error processing {city}: {str(e)}")
                    continue
        
        logger.info(f"Added {added_count} new locations")
        return added_count


def main():
    # Initialize location manager
    manager = LocationManager('E:/Raahi-AI/backend_scripts/data/location_mapping.csv')
    
    # Your curated locations
    curated_locations = {
         "Gilgit-Baltistan": [
            # Major Cities
            "Gilgit", "Skardu", "Hunza", "Shigar", "Ghizer", "Astore", "Khaplu",
            # Hunza Valley
            "Karimabad", "Gulmit", "Passu", "Aliabad", "Nagar", "Hopper", "Hussaini",
            "Altit", "Duikar", "Ganish", "Borith", "Gojal", "Sost",
            # Skardu Region
            "Shigar Valley", "Khaplu Valley", "Deosai Plains", "Satpara Lake", "Kachura Lake",
            "Shangrila Resort", "Manthokha Waterfall", "Kasumbar Lake", "Bara Valley",
            # Astore Valley
            "Rama Lake", "Rama Meadow", "Rupal Valley", "Tarashing", "Minimarg",
            # Ghizer Region
            "Phandar Valley", "Phandar Lake", "Yasin Valley", "Darkut", "Ishkoman Valley",
            "Gupis", "Chatorkhand", "Teru",
            # Nagar Valley
            "Hispar", "Hoper Valley", "Minapin", "Rakaposhi Base Camp", "Golden Peak Base Camp",
            # Special Areas
            "Fairy Meadows", "Nanga Parbat Base Camp", "Rush Lake", "Naltar Valley",
            "Naltar Lakes", "Kutwal Lake", "Attabad Lake", "Borith Lake", "Rush Peak"
        ],
        "KPK Highlands": [
            # Major Cities
            "Chitral", "Swat", "Kalam", "Malam Jabba", "Bahrain", "Mingora",
            "Dir", "Kumrat Valley", "Mahodand Lake",
            # Chitral Region
            "Upper Chitral", "Lower Chitral", "Garam Chashma", "Bumburet",
            "Rumbur", "Birir", "Mastuj", "Booni", "Yarkhun Valley", "Terich Mir Base Camp",
            "Shandur Top", "Kalash Valley", "Ayun", "Drosh",
            # Swat Valley
            "Madyan", "Mankial", "Gabin Jabba", "Ushu Forest", "Matiltan",
            "Utror", "Gabral", "Swat Kohistan", "Marghazar", "Fizagat",
            "Miandam", "Bahrain", "Serai", "Fatehpur", "Khwazakhela",
            # Dir Region
            "Upper Dir", "Lower Dir", "Kumrat", "Jahaz Banda", "Katora Lake",
            "Sheringal", "Lowari Top", "Talash", "Dir Kohistan",
            # Special Areas
            "Kundol Lake", "Spin Khwar", "Daral Lake", "Kandol Lake",
            "Mahudand Lake", "Izmis Lake", "Bashigram Lake", "Char Dara",
            "Lalko", "Bishigram", "Yakhtangi"
        ],
        "Hazara Division": [
            # Major Cities
            "Abbottabad", "Mansehra", "Naran", "Kaghan", "Shogran", "Balakot",
            "Havelian", "Garhi Habibullah", "Oghi",
            # Kaghan Valley
            "Lake Saiful Muluk", "Babusar Top", "Lulusar Lake", "Lalazar",
            "Batakundi", "Jalkhad", "Gittidas", "Lake Dudipat", "Besal",
            "Noori Top", "Malika Parbat Base", "Pyala Lake", "Ansoo Lake",
            # Shogran Area
            "Siri Paye", "Makra Peak", "Musa ka Musalla", "Paye Meadows",
            # Abbottabad Region
            "Thandiani", "Galiyat", "Shimla Hill", "Miranjani Top",
            "Kalabagh", "Nawanshehr", "Dhamtour", "Sherwan",
            # Special Areas
            "Kunhar River", "Paras", "Mahandri", "Kawai",
            "Siran Valley", "Kund Bangla", "Kamal Ban Forest"
        ],
        "Murree & Galyat": [
            # Murree Region
            "Murree", "New Murree", "Kashmir Point", "Pindi Point",
            "Mall Road Murree", "Patriata", "Bhurban", "Sunny Bank",
            "Gharial Garden", "Murree Hills", "Masyari",
            # Galyat Region
            "Nathiagali", "Ayubia", "Dunga Gali", "Changla Gali",
            "Khanspur", "Khaira Gali", "Toheed Abad", "Kalabagh",
            # Special Areas
            "Pipeline Track", "Mushkpuri Top", "Miranjani Peak",
            "Ayubia National Park", "Jungle Resort", "Wild Life Park",
            "Samundar Katha Lake", "Barrier Lake", "Green Spot",
            # Scenic Points
            "Golf Ground", "Lawrence College", "Ghora Gali",
            "Charhan", "Darya Gali", "Mokshpuri Top"
        ]
    }
    
    # Add curated locations to database
    print("Adding curated locations...")
    manager.batch_add_curated_locations(curated_locations)
    
    # Save database
    manager.save_database()
    
    # Example: Test dynamic lookup
    print("\n" + "="*50)
    print("Testing dynamic lookup...")
    print("="*50 + "\n")
    
    test_locations = [
        ("Skardu", "Gilgit-Baltistan"),  # Should find in database
        ("Satpara Lake", "Gilgit-Baltistan"),  # New location, should geocode
        ("Minimarg", "Gilgit-Baltistan"),  # New location
    ]
    
    for area, region in test_locations:
        print(f"\nLooking up: {area} in {region}")
        result = manager.lookup_location(area, region)
        if result:
            print(f"  Found: {result['city']}")
            print(f"  Region: {result['parent_region']}")
            print(f"  Elevation: {result['elevation']}m")
            print(f"  Climate: {result['climate_zone']}")
            print(f"  Season: {result['tourist_season']}")
            print(f"  Verified: {result['verified']}")
        else:
            print(f"  Could not find location data")
        
        time.sleep(1)
    
    # Save any new locations added during testing
    manager.save_database()
    
    # Display statistics
    print("\n" + "="*50)
    print("Database Statistics")
    print("="*50)
    print(f"Total locations: {len(manager.locations_df)}")
    print(f"Verified locations: {manager.locations_df['verified'].sum()}")
    print(f"Unverified locations: {(~manager.locations_df['verified']).sum()}")
    print("\nLocations by region:")
    print(manager.locations_df.groupby('parent_region').size())


if __name__ == "__main__":
    main()