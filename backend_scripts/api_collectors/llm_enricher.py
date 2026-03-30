"""
LLM POI Enricher
Uses Ollama (local, unlimited) to generate rich metadata for POIs
Fills in: descriptions, ratings, mood tags, costs, difficulty, etc.
"""

import requests
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
    Enriches POI data using LLM (Ollama - local, unlimited)
    Generates descriptions, ratings, costs, and custom metadata
    """
    
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM enricher
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.2)
        """
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or os.getenv('OLLAMA_MODEL', 'llama3.2:latest')
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                available_models = [m['name'] for m in response.json().get('models', [])]
                if self.model not in available_models:
                    logger.warning(f"⚠️ Model '{self.model}' not found. Available models: {available_models}")
                    logger.warning(f"⚠️ Attempting to use '{self.model}' anyway. Make sure it's installed with: ollama pull {self.model}")
                logger.info(f"✅ LLM Enricher initialized with Ollama (model: {self.model})")
            else:
                raise ConnectionError(f"Ollama API returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"❌ Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running. Install from: https://ollama.com\n"
                f"Then run: ollama pull {self.model}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Ollama: {e}")
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
            
            # Request JSON response format for better parsing
            # Add explicit instruction for JSON output in prompt
            system_prompt = "You are a Pakistani tourism expert. Always respond with valid JSON only, no markdown formatting, no code blocks."
            json_prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no markdown code blocks, no explanatory text. Start directly with { and end with }."
            
            # Ollama API call (streaming response)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": json_prompt
                        }
                    ],
                    "options": {
                        "temperature": 0.1,  # Lower temperature for more consistent output
                    },
                    "format": "json",  # Request JSON format
                    "stream": False  # Disable streaming for simpler parsing
                },
                timeout=120  # Ollama can be slower, allow 2 minutes
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            # Parse response - Ollama may return streaming format (multiple JSON lines)
            response_text = ""
            response_text_raw = response.text
            
            # Try to parse as single JSON first
            try:
                response_data = json.loads(response_text_raw)
                response_text = response_data.get('message', {}).get('content', '')
            except json.JSONDecodeError:
                # If that fails, it's likely streaming format (multiple JSON objects, one per line)
                logger.debug("Parsing streaming response format")
                lines = response_text_raw.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if 'message' in chunk and 'content' in chunk.get('message', {}):
                            response_text += chunk['message']['content']
                        elif 'content' in chunk:
                            # Sometimes content is directly in chunk
                            response_text += chunk.get('content', '')
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
                
                if not response_text:
                    logger.error(f"Could not extract content. Raw response (first 1000 chars):\n{response_text_raw[:1000]}")
                    raise Exception(f"Could not extract content from Ollama streaming response")
            
            if not response_text:
                raise Exception("Empty response from Ollama")
            
            # Log raw response for debugging
            logger.info(f"📝 Raw Ollama response (first 800 chars):\n{response_text[:800]}")
            
            # Clean and parse response
            enriched_data = self._parse_llm_response(response_text)
            
            logger.info(f"✅ Enriched: {poi_name}")
            return enriched_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON parse error for {poi_name}: {e}")
            # Try to get response_text from the exception context
            try:
                response_text = response.text if 'response' in locals() else "Could not retrieve response"
                logger.warning(f"📝 Full response text:\n{response_text[:2000]}")
            except:
                pass
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
- Do NOT include comments (//) in the JSON output - only valid JSON syntax
"""
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        Parse LLM response, handling markdown formatting and extra text
        
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
        
        # Try to parse directly first (in case it's clean JSON)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # If direct parse fails, extract JSON object
            pass
        
        # Extract JSON object if there's extra text
        # Find the first { and last } to extract just the JSON
        first_brace = text.find('{')
        if first_brace == -1:
            raise json.JSONDecodeError("No JSON object found", text, 0)
        
        # Find the matching closing brace (handle nested objects and strings)
        brace_count = 0
        last_brace = -1
        in_string = False
        escape_next = False
        
        for i in range(first_brace, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_brace = i
                        break
        
        if last_brace == -1:
            # No matching closing brace, try parsing from first brace to end
            logger.warning("⚠️ Could not find matching closing brace, attempting to parse from first brace")
            json_text = text[first_brace:]
        else:
            # Extract just the JSON part
            json_text = text[first_brace:last_brace + 1]
        
        # Try to parse the extracted JSON
        try:
            parsed = json.loads(json_text)
            logger.debug(f"✅ Successfully parsed JSON (extracted {len(json_text)} chars)")
            return parsed
        except json.JSONDecodeError as e:
            # Log the problematic text for debugging
            logger.error(f"❌ JSON parse error at position {e.pos}")
            logger.error(f"Extracted JSON text (first 1000 chars):\n{json_text[:1000]}")
            logger.error(f"Full response text (first 1000 chars):\n{text[:1000]}")
            raise
    
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
        
    except (ValueError, ConnectionError) as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 To test this, you need to:")
        print("1. Install Ollama from: https://ollama.com")
        print("2. Pull the model: ollama pull llama3.2")
        print("3. Make sure Ollama is running (it starts automatically)")
        print("4. Optional: Set OLLAMA_BASE_URL and OLLAMA_MODEL in .env file")


if __name__ == "__main__":
    test_llm_enricher()

