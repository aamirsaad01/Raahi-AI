"""
Shared POI enrichment prompt building, JSON parsing, and fallbacks.
Used by Ollama (llm_enricher) and OpenAI (openai_enricher) pipelines.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def build_enrichment_prompt_old(
    poi_name: str,
    location: str,
    category: str,
    activities: List[str],
    osm_tags: Dict[str, Any],
) -> str:
    elevation = osm_tags.get("ele", "unknown")
    wikipedia = osm_tags.get("wikipedia", "")

    prompt = f"""You are a Pakistani tourism expert with deep knowledge of Northern Pakistan's attractions.

Analyze this location and provide comprehensive, accurate tourism data.

**Location Details:**
- Name: {poi_name}
- Area: {location}, Pakistan
- Category: {category}
- Known Activities: {", ".join(activities) if activities else "general tourism"}
- Elevation: {elevation}m
{f"- Wikipedia: {wikipedia}" if wikipedia else ""}

**Task:** Generate detailed tourism metadata in valid JSON format.

**Required Output (MUST be valid JSON):**
{{
    "description": "Write 2-3 compelling sentences describing what makes this place special. Include key features, historical significance, and why tourists visit. Be specific and engaging.",

    "estimated_rating": "Go throuh the internet and find the rating of this place and return it as a number between 0.0 and 5.0.",

    "category": "{category}",

    "difficulty": "Go through the internet and find the difficulty of this place, consider the elevation and route difficulty, and return it as a string between 'easy', 'moderate', 'hard', 'extreme'.",

    "activities": "Go through the internet and find the activities that you can do at this place and return it as a list of strings or you can choose from the following list: {{activities}}.",

    "mood_tags": "{{osm_tags.mood_tags}}",

    "estimated_cost": "Go through the internet and find the cost of this place and return it as a string between 'Low', 'Medium', 'High', 'Very High'.",

    "cost_range_pkr": {{"min": "Go through the internet and find the minimum cost of this place and return it as a non-negative number", "max": "Go through the internet and find the maximum cost of this place and return it as a non-negative number"}},

    "best_months": "Go through the internet and find the best months to visit this place and return it as a string of months separated by '-'.",

    "avg_duration_hours": "Go through the internet and find the average duration to explore this place and return it as a number between 0.0 and 24.0.",

    "accessibility": "Go through the internet and find the accessibility of this place and return it as a string of the road conditions and vehicle requirements.",

    "permits_required": "Go through the internet and find if permits are required to visit this place and return it as a boolean.",

    "highlights": "Go through the internet and find the highlights or must-see aspects of this place and return it as a list of strings.",

    "nearby_facilities": "Go through the internet and find the nearby facilities of this place and return it as a string of the nearby facilities.",
}}

**Important:**
- Base your response on actual knowledge of Pakistan's tourist sites and the OSM context given.
- If you don't know this specific place, make reasonable estimates based on similar locations in the region.
- Return ONLY valid JSON, no markdown formatting, no explanatory text.
- Be realistic about costs, accessibility, and ratings.
- Consider the region's infrastructure and tourism development level.
- Do NOT include comments (//) in the JSON output - only valid JSON syntax
"""

    return prompt



def build_enrichment_prompt(
    poi_name: str,
    location: str,
    category: str,
    activities: List[str],
    osm_tags: Dict[str, Any],
) -> str:
    elevation = osm_tags.get("ele", "unknown")
    wikipedia = osm_tags.get("wikipedia", "")
    
    # Safely extract variables so they can be properly injected into the f-string
    known_activities = ", ".join(activities) if activities else "general sightseeing"
    moods = osm_tags.get("mood_tags", "family, adventurous, cultural, relaxed, spiritual")

    prompt = f"""You are a Pakistani tourism expert with deep knowledge of local attractions, terrain, and travel logistics.
Analyze this location and provide comprehensive, accurate tourism data based on your internal knowledge.

**Location Details:**
- Name: {poi_name}
- Area: {location}, Pakistan
- Category: {category}
- Known Activities: {known_activities}
- Elevation: {elevation}m
{f"- Wikipedia: {wikipedia}" if wikipedia else ""}

**Task:** Generate detailed tourism metadata.

**Required Output (MUST be valid JSON):**
{{
    "description": "Write 2-3 compelling sentences highlighting key features, historical significance, and why tourists visit. Be specific to the location.",
    "estimated_rating": "Float. Provide a realistic number between 0.0 and 5.0 based on general tourist consensus.",
    "category": "{category}",
    "difficulty": "String. Choose ONLY from: 'easy', 'moderate', 'hard', 'extreme'. Consider elevation and local terrain.",
    "activities": ["Array of strings. Prioritize these if applicable: {known_activities}, plus any others relevant."],
    "mood_tags": ["Array of strings describing the vibe. Choose from or expand upon: {moods}."],
    "estimated_cost": "String. Choose ONLY from: 'Low', 'Medium', 'High', 'Very High'.",
    "cost_range_pkr": {{
        "min": "Integer. Minimum realistic cost to explore this place in PKR. Do not use strings.",
        "max": "Integer. Maximum realistic cost to explore this place in PKR. Do not use strings."
    }},
    "best_months": "String. Formatted as 'Month-Month' (e.g., 'May-October').",
    "avg_duration_hours": "Float. Estimated hours needed to fully explore the site.",
    "accessibility": "Brief string detailing road conditions (e.g., 'Paved road, accessible by sedan' or '4x4 Jeep track only').",
    "permits_required": "Boolean. Set to true if an NOC or local permit is needed, otherwise false.",
    "highlights": ["Array of 3-4 specific must-see features, viewpoints, or historical elements."],
    "nearby_facilities": "Brief string mentioning availability of washrooms, food, or medical help."
}}

**Important Constraints:**
- Rely on your internal knowledge. Do not attempt to browse the internet.
- If specific data is unknown, provide highly educated estimates based on similar locations in {location}.
- Ensure strict JSON formatting. No markdown blocks, no comments (//), no explanatory text outside the JSON.
"""

    return prompt


def parse_enrichment_response(response_text: str) -> Dict[str, Any]:
    text = response_text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    first_brace = text.find("{")
    if first_brace == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)

    brace_count = 0
    last_brace = -1
    in_string = False
    escape_next = False

    for i in range(first_brace, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    last_brace = i
                    break

    if last_brace == -1:
        logger.warning(
            "Could not find matching closing brace, attempting to parse from first brace"
        )
        json_text = text[first_brace:]
    else:
        json_text = text[first_brace : last_brace + 1]

    parsed = json.loads(json_text)
    logger.debug("Successfully parsed JSON (%d chars)", len(json_text))
    return parsed


def default_enrichment(poi_name: str, category: str) -> Dict[str, Any]:
    logger.warning("Using default enrichment for %s", poi_name)

    category_defaults = {
        "nature": {
            "activities": ["hiking", "photography", "sightseeing"],
            "mood_tags": ["adventurous", "family"],
            "difficulty": "moderate",
        },
        "cultural": {
            "activities": ["cultural", "sightseeing", "photography"],
            "mood_tags": ["cultural", "family"],
            "difficulty": "easy",
        },
        "adventure": {
            "activities": ["trekking", "adventure", "photography"],
            "mood_tags": ["adventurous"],
            "difficulty": "hard",
        },
        "religious": {
            "activities": ["religious", "cultural", "sightseeing"],
            "mood_tags": ["spiritual", "cultural"],
            "difficulty": "easy",
        },
        "historical": {
            "activities": ["cultural", "sightseeing", "photography"],
            "mood_tags": ["cultural", "family"],
            "difficulty": "easy",
        },
    }

    defaults = category_defaults.get(category, category_defaults["nature"])

    return {
        "description": (
            f"{poi_name} is a tourist attraction in Northern Pakistan known for its "
            "natural beauty and cultural significance."
        ),
        "estimated_rating": 4.0,
        "category": category,
        "difficulty": defaults["difficulty"],
        "activities": defaults["activities"],
        "mood_tags": defaults["mood_tags"],
        "estimated_cost": "Medium",
        "cost_range_pkr": {"min": 1500, "max": 4000},
        "best_months": "March-October",
        "avg_duration_hours": 3.0,
        "accessibility": "accessible by sedan on paved roads",
        "permits_required": False,
        "highlights": [
            "Scenic natural beauty",
            "Photography opportunities",
            "Local cultural experience",
        ],
        "nearby_facilities": "Basic facilities available in nearby towns",
    }


def normalize_enriched_dict(raw: Dict[str, Any], fallback_category: str) -> Dict[str, Any]:
    """Ensure types and keys match what poi_pipeline._save_poi expects."""

    def _list_str(v: Any, default: List[str]) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v if x is not None]
        return default

    cost = raw.get("cost_range_pkr") or {}
    if not isinstance(cost, dict):
        cost = {}

    min_pkr = cost.get("min", 1500)
    max_pkr = cost.get("max", 4000)
    try:
        min_pkr = int(min_pkr)
        max_pkr = int(max_pkr)
    except (TypeError, ValueError):
        min_pkr, max_pkr = 1500, 4000

    cat = str(raw.get("category") or fallback_category).lower()
    if cat not in ("nature", "cultural", "adventure", "religious", "historical"):
        cat = fallback_category

    diff = str(raw.get("difficulty") or "moderate").lower()
    if diff not in ("easy", "moderate", "hard", "extreme"):
        diff = "moderate"

    ec = str(raw.get("estimated_cost") or "Medium")
    if ec not in ("Low", "Medium", "High", "Very High"):
        ec = "Medium"

    rating = raw.get("estimated_rating", 4.0)
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        rating = 4.0
    rating = max(0.0, min(5.0, rating))

    dur = raw.get("avg_duration_hours", 3.0)
    try:
        dur = float(dur)
    except (TypeError, ValueError):
        dur = 3.0

    permits = raw.get("permits_required", False)
    if not isinstance(permits, bool):
        permits = str(permits).lower() in ("true", "1", "yes")

    return {
        "description": str(raw.get("description") or "")[:8000],
        "estimated_rating": rating,
        "category": cat,
        "difficulty": diff,
        "activities": _list_str(raw.get("activities"), ["sightseeing"]),
        "mood_tags": _list_str(raw.get("mood_tags"), ["family"]),
        "highlights": _list_str(raw.get("highlights"), []),
        "estimated_cost": ec,
        "cost_range_pkr": {"min": min_pkr, "max": max_pkr},
        "best_months": str(raw.get("best_months") or "March-October")[:100],
        "avg_duration_hours": dur,
        "accessibility": str(raw.get("accessibility") or "")[:2000],
        "permits_required": permits,
        "nearby_facilities": str(raw.get("nearby_facilities") or "")[:2000],
    }
