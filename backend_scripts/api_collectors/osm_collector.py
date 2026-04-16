"""
OpenStreetMap Data Collector
Fetches tourist attractions and POIs from OpenStreetMap using Overpass API
100% FREE - No API key required!
"""

import requests
import time
import logging
from typing import List, Dict, Optional, Tuple

from api_collectors.geo_utils import distance_meters
from api_collectors.text_utils import token_set_ratio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OSMCollector:
    """
    Collects Points of Interest from OpenStreetMap
    """
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.timeout = 60
        self.rate_limit_delay = 1  # seconds between requests
    
    def fetch_pois_for_location(
        self, 
        location_name: str, 
        lat: float, 
        lon: float, 
        radius_km: int = 15
    ) -> List[Dict]:
        """
        Fetch tourist attractions from OpenStreetMap around a location
        
        Args:
            location_name: Name of the location (e.g., "Hunza")
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers (default: 15km)
        
        Returns:
            List of POI dictionaries with basic OSM data
        """
        radius_meters = radius_km * 1000
        
        # Overpass QL query - searches for various tourism and nature tags
        query = f"""
        [out:json][timeout:25];
        (
          node["tourism"="attraction"](around:{radius_meters},{lat},{lon});
          node["tourism"="viewpoint"](around:{radius_meters},{lat},{lon});
          node["tourism"="museum"](around:{radius_meters},{lat},{lon});
          node["tourism"="gallery"](around:{radius_meters},{lat},{lon});
          node["natural"="peak"](around:{radius_meters},{lat},{lon});
          node["natural"="waterfall"](around:{radius_meters},{lat},{lon});
          node["natural"="glacier"](around:{radius_meters},{lat},{lon});
          node["natural"="hot_spring"](around:{radius_meters},{lat},{lon});
          node["natural"="valley"](around:{radius_meters},{lat},{lon});
          node["leisure"="park"](around:{radius_meters},{lat},{lon});
          node["historic"](around:{radius_meters},{lat},{lon});
          node["amenity"="place_of_worship"](around:{radius_meters},{lat},{lon});
          way["tourism"="attraction"](around:{radius_meters},{lat},{lon});
          way["tourism"="viewpoint"](around:{radius_meters},{lat},{lon});
          way["natural"="peak"](around:{radius_meters},{lat},{lon});
          way["natural"="waterfall"](around:{radius_meters},{lat},{lon});
          way["leisure"="park"](around:{radius_meters},{lat},{lon});
          relation["tourism"="attraction"](around:{radius_meters},{lat},{lon});
          relation["natural"="peak"](around:{radius_meters},{lat},{lon});
        );
        out center;
        """
        
        try:
            logger.info(f"🌍 Querying OSM for POIs near {location_name}...")
            
            response = requests.post(
                self.overpass_url,
                data={'data': query},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            pois = []
            for element in data.get('elements', []):
                poi = self._parse_osm_element(element, location_name)
                if poi and poi['name'] != 'Unnamed':  # Skip unnamed POIs
                    pois.append(poi)
            
            logger.info(f"✅ Found {len(pois)} raw POIs from OSM for {location_name}")
            
            # Apply micro-level deduplication (Intra-location fixes)
            pois = self._deduplicate_pois(pois)
            
            # Rate limiting - be nice to OSM servers
            time.sleep(self.rate_limit_delay)
            
            return pois
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ OSM request timeout for {location_name}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching from OSM: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return []
    
    def _deduplicate_pois(self, raw_pois: List[Dict], distance_threshold_meters: int = 1500, fuzz_threshold: int = 80) -> List[Dict]:
        """
        Removes crowdsourced duplicates that are physically close to each other.
        Now uses token_set_ratio to ignore word order.
        """
        unique_pois = []
        
        for poi in raw_pois:
            is_duplicate = False
            for existing in unique_pois:
                # 1. Check physical distance (Increased to 1500m for mountainous areas)
                dist = distance_meters(
                    float(poi["latitude"]),
                    float(poi["longitude"]),
                    float(existing["latitude"]),
                    float(existing["longitude"]),
                )
                
                # 2. Check name similarity if they are physically close
                if dist < distance_threshold_meters:
                    # Swapped to token_set_ratio to handle "Viewpoint on Rakaposhi" vs "Rakaposhi Viewpoint"
                    name_similarity = token_set_ratio(poi["name"], existing["name"])
                    
                    if name_similarity > fuzz_threshold:
                        is_duplicate = True
                        # If the new duplicate has more OSM tags, it's likely higher quality data. Replace the old one.
                        if len(poi.get('osm_tags', {})) > len(existing.get('osm_tags', {})):
                            existing.update(poi)
                        break 
                        
            if not is_duplicate:
                unique_pois.append(poi)
                
        removed_count = len(raw_pois) - len(unique_pois)
        if removed_count > 0:
            logger.info(f"🧹 Deduplication removed {removed_count} redundant/overlapping POIs.")
            
        return unique_pois

    def _parse_osm_element(self, element: Dict, location_name: str) -> Optional[Dict]:
        """
        Parse OSM element into our POI format
        """
        tags = element.get('tags', {})
        
        # Get coordinates
        if element['type'] == 'node':
            lat = element.get('lat')
            lon = element.get('lon')
        else:
            # For ways/relations, use center
            center = element.get('center', {})
            lat = center.get('lat')
            lon = center.get('lon')
        
        if not lat or not lon:
            return None
        
        # Extract name (prefer English name, fallback to local name)
        name = tags.get('name:en', tags.get('name', ''))
        if not name or name.strip() == '':
            name = 'Unnamed'
        
        # Determine category from OSM tags
        category = self._determine_category(tags)
        
        # Extract initial activities from tags
        activities = self._extract_activities(tags, category)
        
        # Create unique OSM ID
        osm_id = f"{element['type']}_{element['id']}"
        
        return {
            'osm_id': osm_id,
            'osm_type': element['type'],
            'name': name.strip(),
            'location_name': location_name,
            'latitude': float(lat),
            'longitude': float(lon),
            'category': category,
            'activities': activities,
            'osm_tags': tags  # Keep raw tags for reference
        }
    
    def _determine_category(self, tags: Dict) -> str:
        """Map OSM tags to our category system"""
        if tags.get('natural') in ['peak', 'glacier', 'waterfall', 'valley', 'hot_spring']:
            return 'nature'
        if tags.get('amenity') == 'place_of_worship':
            return 'religious'
        if tags.get('historic'):
            return 'historical'
        if tags.get('tourism') in ['museum', 'gallery']:
            return 'cultural'
        if tags.get('sport') or tags.get('climbing'):
            return 'adventure'
        if tags.get('tourism') in ['viewpoint', 'attraction']:
            return 'nature'
        return 'nature' 
    
    def _extract_activities(self, tags: Dict, category: str) -> List[str]:
        """Extract potential activities from OSM tags"""
        activities = []
        
        if tags.get('natural') == 'peak':
            activities.extend(['hiking', 'photography', 'trekking'])
        if tags.get('natural') == 'waterfall':
            activities.extend(['photography', 'hiking', 'sightseeing'])
        if tags.get('natural') == 'glacier':
            activities.extend(['photography', 'trekking', 'adventure'])
        if tags.get('natural') == 'hot_spring':
            activities.extend(['relaxation', 'photography'])
        if tags.get('tourism') == 'viewpoint':
            activities.extend(['photography', 'sightseeing'])
        if tags.get('tourism') in ['museum', 'gallery']:
            activities.extend(['cultural', 'sightseeing'])
        if tags.get('sport') == 'skiing':
            activities.append('skiing')
        if tags.get('sport') == 'climbing':
            activities.extend(['rock_climbing', 'adventure'])
        if tags.get('leisure') == 'park':
            activities.extend(['picnic', 'family', 'relaxation'])
        if tags.get('amenity') == 'place_of_worship':
            activities.extend(['cultural', 'religious', 'sightseeing'])
            
        if not activities:
            if category == 'nature':
                activities = ['sightseeing', 'photography']
            elif category == 'cultural':
                activities = ['cultural', 'sightseeing']
            elif category == 'adventure':
                activities = ['adventure', 'hiking']
            elif category == 'religious':
                activities = ['religious', 'cultural']
            else:
                activities = ['sightseeing']
        
        seen = set()
        unique_activities = []
        for activity in activities:
            if activity not in seen:
                seen.add(activity)
                unique_activities.append(activity)
        
        return unique_activities


def test_osm_collector():
    collector = OSMCollector()
    test_location = {
        'name': 'Hunza',
        'lat': 36.2993187,
        'lon': 74.613428
    }
    print(f"\n{'='*60}")
    print(f"Testing OSM Collector for {test_location['name']}")
    print(f"{'='*60}\n")
    pois = collector.fetch_pois_for_location(test_location['name'], test_location['lat'], test_location['lon'])
    
    if pois:
        print(f"\n✅ Found {len(pois)} POIs:")
        for i, poi in enumerate(pois[:5], 1):
            print(f"\n{i}. {poi['name']}")
            print(f"   Category: {poi['category']}")
            print(f"   Activities: {', '.join(poi['activities'])}")
            print(f"   Location: ({poi['latitude']:.4f}, {poi['longitude']:.4f})")
    else:
        print("❌ No POIs found")


if __name__ == "__main__":
    test_osm_collector()