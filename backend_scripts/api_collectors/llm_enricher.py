"""
LLM POI Enricher
Uses Google Gemini (FREE) to generate rich metadata for POIs
Fills in: descriptions, ratings, mood tags, costs, difficulty, etc.
"""

import google.generativeai as genai
import json
import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class POIEnricher:
    """
    Enriches POI data using LLM (Google Gemini)
    Generates descriptions, ratings, costs, and custom metadata
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM enricher
        
        Args:
            api_key: Gemini API key (optional, reads from env if not provided)
        """
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError(
                "Gemini API key not found! "
                "Set GEMINI_API_KEY in .env file or pass it as argument"
            )
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ LLM Enricher initialized with Gemini")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            raise
    
    def enrich_poi(self, poi_data: Dict) -> Dict:
        """
        Enrich POI data with LLM-generated content
        
        Args:
            poi_data: Basic POI info from OSM {name, location_name, category, activities, osm_tags}
        
        Returns:
            Dictionary with enriched data (description, rating, mood_tags, costs, etc.)
        """
        poi_name = poi_data.get('name', 'Unknown')
        location = poi_data.get('location_name', 'Pakistan')
        category = poi_data.get('category', 'nature')
        initial_activities = poi_data.get('activities', [])
        osm_tags = poi_data.get('osm_tags', {})
        
        # Create context-rich prompt
        prompt = self._create_enrichment_prompt(
            poi_name, location, category, initial_activities, osm_tags
        )
        
        try:
            logger.info(f"🤖 Enriching: {poi_name} in {location}")
            
            response = self.model.generate_content(prompt)
            
            # Clean and parse response
            enriched_data = self._parse_llm_response(response.text)
            
            logger.info(f"✅ Enriched: {poi_name}")
            return enriched_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON parse error for {poi_name}: {e}")
            return self._default_enrichment(poi_name, category)
        except Exception as e:
            logger.error(f"❌ LLM error for {poi_name}: {e}")
            return self._default_enrichment(poi_name, category)
    
    def _create_enrichment_prompt(
        self,
        poi_name: str,
        location: str,
        category: str,
        activities: list,
        osm_tags: dict
    ) -> str:
        """Create detailed prompt for LLM"""
        
        # Extract additional context from OSM tags
        elevation = osm_tags.get('ele', 'unknown')
        wikipedia = osm_tags.get('wikipedia', '')
        
        prompt = f"""You are a Pakistani tourism expert with deep knowledge of Northern Pakistan's attractions.

Analyze this location and provide comprehensive, accurate tourism data.

**Location Details:**
- Name: {poi_name}
- Area: {location}, Pakistan
- Category: {category}
- Known Activities: {', '.join(activities) if activities else 'general tourism'}
- Elevation: {elevation}m
{f"- Wikipedia: {wikipedia}" if wikipedia else ""}

**Task:** Generate detailed tourism metadata in valid JSON format.

**Required Output (MUST be valid JSON):**
{{
    "description": "Write 2-3 compelling sentences describing what makes this place special. Include key features, historical significance, and why tourists visit. Be specific and engaging.",
    
    "estimated_rating": 4.5,
    // Rating scale (1.0-5.0):
    // 5.0 = World-famous (Fairy Meadows, Hunza Valley)
    // 4.5-4.9 = Very popular tourist destination
    // 4.0-4.4 = Popular local attraction
    // 3.5-3.9 = Worth visiting but less known
    // 3.0-3.4 = Minor attraction
    // Below 3.0 = Not recommended
    
    "category": "{category}",
    // Keep same unless clearly wrong. Options: nature, cultural, adventure, religious, historical
    
    "difficulty": "easy",
    // easy = accessible to everyone, paved roads
    // moderate = some hiking/rough roads, average fitness needed
    // hard = significant trekking, 4x4 required, good fitness
    // extreme = technical climbing, serious hiking, expedition level
    
    "activities": ["activity1", "activity2", "activity3"],
    // Choose 3-5 from: hiking, photography, camping, rock_climbing, skiing, 
    // sightseeing, cultural, religious, picnic, boating, fishing, trekking, adventure
    
    "mood_tags": ["tag1", "tag2"],
    // Choose 2-3 from: adventurous, relaxed, romantic, family, cultural, spiritual
    
    "estimated_cost": "Medium",
    // Low = Under 2000 PKR per person (basic sightseeing, free entry)
    // Medium = 2000-5000 PKR (includes transport, food, basic accommodation)
    // High = 5000-15000 PKR (guides, camping gear, permits)
    // Very High = 15000+ PKR (expedition, specialized equipment)
    
    "cost_range_pkr": {{"min": 1000, "max": 3000}},
    // Realistic per-person costs including transport from nearest city, entry, basic food
    
    "best_months": "March-October",
    // Consider weather, road access, snow conditions
    // Options: "All year", "March-October", "June-September", "December-February", specific months
    
    "avg_duration_hours": 4.0,
    // Realistic time tourists spend: viewing, hiking, exploring
    // 1-2 hours = quick stop/viewpoint
    // 3-5 hours = half-day trip
    // 6-8 hours = full day
    // 12+ hours = overnight/multi-day
    
    "accessibility": "accessible by sedan on paved roads",
    // Be specific: "sedan friendly", "4x4 required", "2 hour hike from road", 
    // "technical climb", "helicopter access only"
    
    "permits_required": false,
    // true if: restricted area, national park entry, special permission needed
    
    "highlights": [
        "Key feature or must-see aspect 1",
        "Key feature or must-see aspect 2",
        "Key feature or must-see aspect 3"
    ],
    // 3-4 specific highlights that make this place special
    
    "nearby_facilities": "Hotels in nearby town, restaurants available, fuel stations within 20km"
    // Describe: accommodation, food, fuel, mobile coverage, ATMs
}}

**Important:**
- Base your response on actual knowledge of Pakistan's tourist sites
- If you don't know this specific place, make reasonable estimates based on similar locations in the region
- Return ONLY valid JSON, no markdown formatting, no explanatory text
- Be realistic about costs, accessibility, and ratings
- Consider the region's infrastructure and tourism development level
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        Parse LLM response, handling markdown formatting
        
        Args:
            response_text: Raw LLM output
        
        Returns:
            Parsed dictionary
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        if text.startswith('```json'):
            text = text[7:]  # Remove ```json
        elif text.startswith('```'):
            text = text[3:]  # Remove ```
        
        if text.endswith('```'):
            text = text[:-3]  # Remove trailing ```
        
        text = text.strip()
        
        # Parse JSON
        return json.loads(text)
    
    def _default_enrichment(self, poi_name: str, category: str) -> Dict:
        """
        Fallback enrichment if LLM fails
        
        Args:
            poi_name: POI name
            category: POI category
        
        Returns:
            Basic enrichment dictionary
        """
        logger.warning(f"Using default enrichment for {poi_name}")
        
        # Category-based defaults
        category_defaults = {
            'nature': {
                'activities': ['hiking', 'photography', 'sightseeing'],
                'mood_tags': ['adventurous', 'family'],
                'difficulty': 'moderate'
            },
            'cultural': {
                'activities': ['cultural', 'sightseeing', 'photography'],
                'mood_tags': ['cultural', 'family'],
                'difficulty': 'easy'
            },
            'adventure': {
                'activities': ['trekking', 'adventure', 'photography'],
                'mood_tags': ['adventurous'],
                'difficulty': 'hard'
            },
            'religious': {
                'activities': ['religious', 'cultural', 'sightseeing'],
                'mood_tags': ['spiritual', 'cultural'],
                'difficulty': 'easy'
            },
            'historical': {
                'activities': ['cultural', 'sightseeing', 'photography'],
                'mood_tags': ['cultural', 'family'],
                'difficulty': 'easy'
            }
        }
        
        defaults = category_defaults.get(category, category_defaults['nature'])
        
        return {
            "description": f"{poi_name} is a tourist attraction in Northern Pakistan known for its natural beauty and cultural significance.",
            "estimated_rating": 4.0,
            "category": category,
            "difficulty": defaults['difficulty'],
            "activities": defaults['activities'],
            "mood_tags": defaults['mood_tags'],
            "estimated_cost": "Medium",
            "cost_range_pkr": {"min": 1500, "max": 4000},
            "best_months": "March-October",
            "avg_duration_hours": 3.0,
            "accessibility": "accessible by sedan on paved roads",
            "permits_required": False,
            "highlights": [
                "Scenic natural beauty",
                "Photography opportunities",
                "Local cultural experience"
            ],
            "nearby_facilities": "Basic facilities available in nearby towns"
        }


# Test function
def test_llm_enricher():
    """Test the LLM enricher with sample data"""
    try:
        enricher = POIEnricher()
        
        # Test POI data
        test_poi = {
            'name': 'Fairy Meadows',
            'location_name': 'Gilgit-Baltistan',
            'category': 'nature',
            'activities': ['hiking', 'camping', 'photography'],
            'osm_tags': {'natural': 'grassland', 'tourism': 'camp_site'}
        }
        
        print(f"\n{'='*60}")
        print(f"Testing LLM Enricher")
        print(f"{'='*60}\n")
        print(f"Input POI: {test_poi['name']}")
        
        result = enricher.enrich_poi(test_poi)
        
        print(f"\n✅ Enrichment Result:")
        print(f"\nDescription: {result['description']}")
        print(f"Rating: {result['estimated_rating']}/5.0")
        print(f"Difficulty: {result['difficulty']}")
        print(f"Cost: {result['estimated_cost']} ({result['cost_range_pkr']['min']}-{result['cost_range_pkr']['max']} PKR)")
        print(f"Activities: {', '.join(result['activities'])}")
        print(f"Mood Tags: {', '.join(result['mood_tags'])}")
        print(f"Best Months: {result['best_months']}")
        print(f"Duration: {result['avg_duration_hours']} hours")
        print(f"\nHighlights:")
        for highlight in result['highlights']:
            print(f"  • {highlight}")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 To test this, you need to:")
        print("1. Get a free Gemini API key from: https://makersuite.google.com/app/apikey")
        print("2. Add it to your .env file: GEMINI_API_KEY=your_key_here")


if __name__ == "__main__":
    test_llm_enricher()

