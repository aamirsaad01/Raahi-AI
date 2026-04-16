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

from api_collectors.poi_enrichment_common import (
    build_enrichment_prompt,
    default_enrichment,
    normalize_enriched_dict,
    parse_enrichment_response,
)

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
        
        prompt = build_enrichment_prompt(
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
            
            enriched_data = normalize_enriched_dict(
                parse_enrichment_response(response_text), category
            )

            logger.info(f"✅ Enriched: {poi_name}")
            return enriched_data

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON parse error for {poi_name}: {e}")
            try:
                response_text = (
                    response.text if "response" in locals() else "Could not retrieve response"
                )
                logger.warning(f"📝 Full response text:\n{response_text[:2000]}")
            except Exception:
                pass
            return normalize_enriched_dict(
                default_enrichment(poi_name, category), category
            )
        except Exception as e:
            logger.error(f"❌ LLM error for {poi_name}: {e}")
            return normalize_enriched_dict(
                default_enrichment(poi_name, category), category
            )


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

