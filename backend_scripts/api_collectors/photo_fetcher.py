"""
Photo Fetcher
Fetches photos from Unsplash (FREE API)
Alternative: Can be extended to support other free photo sources
"""

import requests
import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhotoFetcher:
    """
    Fetches photos for POIs from Unsplash API (FREE tier)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize photo fetcher
        
        Args:
            api_key: Unsplash Access Key (optional, reads from env)
        """
        self.access_key = api_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.base_url = "https://api.unsplash.com/search/photos"
        self.rate_limit_delay = 1  # seconds between requests
        
        if self.access_key:
            logger.info("✅ Photo Fetcher initialized with Unsplash API")
        else:
            logger.warning("⚠️ No Unsplash API key - photo fetching will be skipped")
    
    def fetch_photos(
        self,
        location_name: str,
        area_name: str,
        max_photos: int = 3
    ) -> List[Dict]:
        """
        Fetch photos from Unsplash
        
        Args:
            location_name: POI name (e.g., "Fairy Meadows")
            area_name: Region name (e.g., "Gilgit-Baltistan")
            max_photos: Maximum number of photos to fetch (default: 3)
        
        Returns:
            List of photo dictionaries with URLs and attribution
        """
        if not self.access_key:
            logger.debug("Skipping photo fetch - no API key")
            return []
        
        # Construct search query
        query = f"{location_name} {area_name} Pakistan"
        
        try:
            logger.info(f"📸 Fetching photos for: {location_name}")
            
            response = requests.get(
                self.base_url,
                params={
                    'query': query,
                    'per_page': max_photos,
                    'orientation': 'landscape',
                    'content_filter': 'high'  # Family-friendly content only
                },
                headers={'Authorization': f'Client-ID {self.access_key}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                photos = []
                
                for photo in data.get('results', []):
                    photos.append({
                        'url_full': photo['urls']['full'],
                        'url_regular': photo['urls']['regular'],
                        'url_small': photo['urls']['small'],
                        'url_thumb': photo['urls']['thumb'],
                        'photographer': photo['user']['name'],
                        'photographer_url': photo['user']['links']['html'],
                        'photo_url': photo['links']['html'],
                        'description': photo.get('description', photo.get('alt_description', '')),
                        'width': photo['width'],
                        'height': photo['height']
                    })
                
                logger.info(f"✅ Found {len(photos)} photos for {location_name}")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                return photos
            
            elif response.status_code == 401:
                logger.error("❌ Invalid Unsplash API key")
                return []
            
            elif response.status_code == 403:
                logger.warning("⚠️ Unsplash rate limit exceeded")
                return []
            
            else:
                logger.warning(f"⚠️ Unsplash returned status {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ Photo fetch timeout for {location_name}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Photo fetch error: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching photos: {e}")
            return []
    
    def fetch_fallback_photos(
        self,
        category: str,
        region: str
    ) -> List[Dict]:
        """
        Fetch generic photos based on category when specific location has no photos
        
        Args:
            category: POI category (nature, cultural, etc.)
            region: Region name
        
        Returns:
            List of generic relevant photos
        """
        if not self.access_key:
            return []
        
        # Generic search terms based on category
        category_queries = {
            'nature': f"{region} mountains Pakistan landscape",
            'cultural': f"{region} Pakistan culture architecture",
            'adventure': f"{region} Pakistan trekking hiking",
            'religious': f"{region} Pakistan mosque shrine",
            'historical': f"{region} Pakistan historical fort"
        }
        
        query = category_queries.get(category, f"{region} Pakistan")
        
        try:
            response = requests.get(
                self.base_url,
                params={
                    'query': query,
                    'per_page': 2,
                    'orientation': 'landscape'
                },
                headers={'Authorization': f'Client-ID {self.access_key}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                photos = []
                
                for photo in data.get('results', [])[:2]:  # Max 2 fallback photos
                    photos.append({
                        'url_regular': photo['urls']['regular'],
                        'url_thumb': photo['urls']['thumb'],
                        'photographer': photo['user']['name'],
                        'photo_url': photo['links']['html'],
                        'description': f"Generic {category} photo for {region}",
                        'is_fallback': True
                    })
                
                time.sleep(self.rate_limit_delay)
                return photos
            
            return []
            
        except Exception as e:
            logger.warning(f"Fallback photo fetch failed: {e}")
            return []


# Test function
def test_photo_fetcher():
    """Test the photo fetcher"""
    fetcher = PhotoFetcher()
    
    if not fetcher.access_key:
        print("\n⚠️ No Unsplash API key found!")
        print("\n💡 To test photo fetching:")
        print("1. Get free API key: https://unsplash.com/developers")
        print("2. Add to .env: UNSPLASH_ACCESS_KEY=your_key_here")
        print("\nNote: Photo fetching is OPTIONAL - the system works without it!")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing Photo Fetcher")
    print(f"{'='*60}\n")
    
    # Test with a known location
    test_locations = [
        ("Hunza Valley", "Gilgit-Baltistan"),
        ("Fairy Meadows", "Gilgit-Baltistan"),
    ]
    
    for location, region in test_locations:
        print(f"\nFetching photos for: {location}, {region}")
        photos = fetcher.fetch_photos(location, region, max_photos=2)
        
        if photos:
            print(f"✅ Found {len(photos)} photos:")
            for i, photo in enumerate(photos, 1):
                print(f"\n  {i}. {photo['description']}")
                print(f"     Photographer: {photo['photographer']}")
                print(f"     URL: {photo['url_thumb']}")
        else:
            print("❌ No photos found")
        
        print("\n" + "-"*60)


if __name__ == "__main__":
    test_photo_fetcher()

