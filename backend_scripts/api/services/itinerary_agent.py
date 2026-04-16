"""
Itinerary Agent Service – Hybrid RAG with OpenAI
Retrieves POIs + NDMA hazards from the database, fetches a real-world
drive-time matrix via Geoapify, then asks gpt-4o-mini to compose a
richly detailed, geographically paced travel plan.

Supports both single-city hubs and multi-city corridor (road-trip) mode.
"""

import json
import logging
import math
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.db_helper import DatabaseHelper
from api.services.poi_matcher import POIMatcher
from api.services.routing_service import RoutingService

logger = logging.getLogger(__name__)

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(dotenv_path=os.path.join(repo_root, ".env"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── System prompt ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are **Raahi**, an elite Pakistani travel planner AI that creates
rich, hour-by-hour trip plans – the kind a professional tour operator
would hand to a client.

### CORE PHILOSOPHY
- **Maximise every day.**  Each day should have **6-10 time slots** covering
  the full waking window (≈ 06:00 AM – 10:00 PM).
- Slots are **actions, not just places.**  Write each one as something the
  traveller will *do*:  "Hiking", "Breakfast", "Boating", "Photography",
  "Check-in", "Scenic Drive", "Shopping", "Swimming", "Rest", "Lunch",
  "Dinner", "Cultural Visit", "Camping Setup", "Stargazing", etc.
- Include **practical life-slots** every day: Breakfast, Lunch, Dinner,
  Hotel Check-in / Check-out, Rest / Free Time.  Set `poi_id` to null
  for these if no matching POI exists.
- Between POI-based activities, add **transition / scenic-drive** slots
  when travel time exceeds 15 minutes.  These count as activities too
  (e.g., activity_type = "Scenic Drive", location_name = "KKH Scenic
  Route to Attabad Lake").

### HARD RULES
1. For **sightseeing, hiking, boating, cultural visits, photography**, and
   all attraction-based activities you MUST use **only** the POIs supplied
   in <retrieved_pois>.  Never invent or hallucinate any attraction POI.
   For **Breakfast, Lunch, Dinner, and Check-in / Check-out** slots you
   SHOULD name a **real, well-known restaurant, hotel, or guest house** in
   the area – use your knowledge of Pakistan's hospitality scene.  These
   slots always have `poi_id: null`.
2. Every `poi_id` you output **must** exactly match a `poi_id` from the
   supplied list.  Meal and accommodation slots must have `poi_id: null`.
3. If NDMA hazard alerts are provided in <active_hazards>, weave relevant
   safety advisories into `trip_overview` and the affected day's
   `day_summary`.
4. Return **only** a single JSON object – no markdown fences, no prose.
5. All cost figures must be in PKR and realistic for Pakistan.
6. Respect the user's stated mood, budget, and duration.
7. The `description` for each time slot must be a vivid, narrative
   paragraph (3-5 sentences) covering what the traveller will experience,
   any history or cultural context, and why it fits their mood.
8. `packing_recommendations` should list 5-8 items with a short reason
   each, tailored to the destination, season, and activities.
9. You have been provided with a **Drive-Time Matrix** for all POIs.
   Use it to pace the itinerary realistically.  Do NOT schedule
   back-to-back activities 2+ hours apart by road unless a transit slot
   sits between them.  Include a `transit_instruction` describing the
   drive between consecutive stops.
10. Estimate a global `estimated_transport_cost_pkr` based on total km
    driven (≈ PKR 25/km fuel/hire cost).

### NO-REPEAT / VARIETY RULES
11. **NEVER repeat the same POI** (same `poi_id`) on more than one day.
    Each attraction-based time slot must feature a **unique** POI.
    If the supplied POI list is smaller than the number of days, it is
    acceptable to have fewer POI-based slots on some days – fill those
    gaps with scenic drives, rest, or longer meal experiences instead.
12. **Vary restaurants and hotels across days.**  Do NOT use the same
    restaurant name for Lunch or Dinner on multiple days.  If the area
    has limited options, at least alternate between 2-3 different names.
13. **Vary activity types across the day.**  Avoid scheduling two
    consecutive slots with the identical `activity_type` (e.g., two
    back-to-back "Photography" slots).  Mix hiking, sightseeing,
    photography, cultural visits, etc.

### GEOGRAPHIC ROUTING RULES (anti-backtracking)
Each POI has a `suggested_visit_order` number.  This order forms a
geographically efficient loop that **minimises backtracking**.
- **Schedule POIs in ascending `suggested_visit_order`.**  You may group
  several consecutive-order POIs into the same day, but never jump
  backwards to a lower order on a later day.
- **Hotel / Check-in each night must be geographically close to the LAST
  POI visited that day** — do NOT send the traveller back to a distant
  hotel they used on a previous day unless they are still in the same
  area.
- If the traveller passes through an area on the way to a further
  destination, schedule that area's POIs **on the way**, not as a
  return trip later.

### DAILY STRUCTURE GUIDELINE
A well-planned day should roughly follow this rhythm:
  Early Morning  →  Breakfast → Hotel Check-out → Transition to the next location
  Morning        →  Main activity #1 (hike, sightseeing, cultural visit …)
  Late Morning   →  Transition / secondary activity
  Afternoon      →  Lunch → Main activity #2
  Late Afternoon →  Activity #3 or free time / shopping
  Evening        →  Dinner → Leisure / Night activity  
  Night          →  Hotel Check-in
Adapt freely based on location, daylight, and weather.

### MULTI-CITY ROAD-TRIP RULES (when `route_order` is present on POIs)
14. You are planning a **multi-location road trip**.  Group POIs by their `route_order` and schedule them on consecutive days following the geographical sequence.
15. DO NOT bounce the traveller between distant cities on the same day.
16. Each day's `theme_title` should mention the city/region being explored (e.g., "Day 2 – Exploring the Hunza Valley").
17. Transit-heavy days should describe the scenic drive itself as a highlight in `day_summary`.

### OUTPUT SCHEMA (strict – do not add or remove keys)
```json
{
  "itinerary_title": "string",
  "trip_overview": "string (2-3 paragraphs)",
  "total_estimated_cost_pkr": { "min": int, "max": int },
  "estimated_transport_cost_pkr": int,
  "packing_recommendations": ["Item – reason", ...],
  "days": [
    {
      "day_number": int,
      "theme_title": "string",
      "day_summary": "string (2-3 sentences summarising the day's plan)",
      "time_slots": [
        {
          "time_of_day": "Early Morning | Morning | Late Morning | Afternoon | Late Afternoon | Evening | Night",
          "start_time": "HH:MM AM/PM",
          "end_time": "HH:MM AM/PM",
          "activity_type": "string – action verb/noun, e.g. Hiking, Breakfast, Boating, Photography, Check-in, Scenic Drive, Shopping, Rest, Lunch, Dinner, Cultural Visit",
          "poi_id": "int or null (null for meals, rest, drives, check-in/out)",
          "location_name": "string – the venue / place name",
          "description": "string (3-5 vivid sentences)",
          "estimated_cost_pkr": "string (number as string, '0' when free)",
          "travel_tips": "string",
          "transit_from_previous_mins": "int or null",
          "transit_distance_km": "float or null",
          "transit_instruction": "string or null"
        }
      ]
    }
  ]
}
```
"""


class ItineraryAgent:
    """Hybrid RAG itinerary generator powered by OpenAI."""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set – cannot initialise ItineraryAgent")
        self.client = OpenAI(api_key=api_key)
        self.db = DatabaseHelper()
        self.matcher = POIMatcher()
        self.routing = RoutingService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, user_prefs: Dict) -> Dict:
        """End-to-end itinerary generation.

        Accepts an optional ``corridor_id`` key in *user_prefs*.  When
        present the agent collects POIs from every city on that corridor;
        otherwise it falls back to single-city mode.
        """
        try:
            corridor = self._resolve_corridor(user_prefs)

            if corridor is not None:
                return self._generate_corridor(user_prefs, corridor)

            return self._generate_single_city(user_prefs)

        except Exception as exc:
            logger.exception("ItineraryAgent.generate failed")
            return {"success": False, "error": str(exc)}

    def close(self):
        self.db.close()

    # ------------------------------------------------------------------
    # Single-city flow (original)
    # ------------------------------------------------------------------

    def _generate_single_city(self, user_prefs: Dict) -> Dict:
        location = self.db.get_location_by_city(user_prefs["destination"])
        if not location:
            return {
                "success": False,
                "error": f"Location '{user_prefs['destination']}' not found",
                "suggestion": "Check spelling or try a different location",
            }

        pois = self._retrieve_pois(location, user_prefs)
        if not pois:
            return {
                "success": False,
                "error": "No attractions found for this location",
                "suggestion": "Try different preferences or another destination",
            }

        self._assign_visit_order(
            pois,
            start_lat=float(location["latitude"]),
            start_lon=float(location["longitude"]),
        )

        hazards = self._retrieve_hazards(location)
        transit_matrix = self.routing.get_poi_matrix(pois)

        user_prompt = self._build_user_prompt(
            user_prefs, pois, hazards, location, transit_matrix
        )

        raw_json = self._call_llm(user_prompt)
        itinerary_payload = self._parse_and_validate(raw_json, pois)
        self._enrich_slots_with_coordinates(itinerary_payload, pois)
        self._recompute_transit_from_slot_coordinates(itinerary_payload)
        itinerary_id = self._persist(itinerary_payload, user_prefs, location)

        return {
            "success": True,
            "itinerary_id": itinerary_id,
            **itinerary_payload,
            "destination": location["city"],
            "region": location["parent_region"],
            "num_days": user_prefs["days"],
            "total_budget": user_prefs["budget"],
            "num_people": user_prefs.get("num_people", 1),
            "location_info": {
                "latitude": float(location["latitude"]),
                "longitude": float(location["longitude"]),
                "elevation": float(location["elevation"]) if location.get("elevation") else None,
                "climate_zone": location.get("climate_zone"),
                "tourist_season": location.get("tourist_season"),
            },
        }

    # ------------------------------------------------------------------
    # Multi-city corridor flow
    # ------------------------------------------------------------------

    def _resolve_corridor(self, user_prefs: Dict) -> Optional[Dict]:
        """Return a corridor dict if the request includes a corridor_id."""
        cid = user_prefs.get("corridor_id")
        if cid is None:
            return None
        try:
            return self.db.get_corridor_by_id(int(cid))
        except Exception:
            return None

    def _generate_corridor(self, user_prefs: Dict, corridor: Dict) -> Dict:
        """Generate a multi-city road-trip itinerary."""
        pois = self._retrieve_corridor_pois(corridor, user_prefs)
        if not pois:
            return {
                "success": False,
                "error": f"No attractions found along corridor '{corridor['name']}'",
                "suggestion": "Try different preferences or another corridor",
            }

        # Use the first stop's location for hazard/weather context
        primary_location = self._primary_location_from_corridor(corridor)
        hazards = self._retrieve_hazards(primary_location) if primary_location else []

        transit_matrix = self.routing.get_poi_matrix(pois)

        user_prompt = self._build_corridor_prompt(
            user_prefs, pois, hazards, corridor, transit_matrix
        )

        raw_json = self._call_llm(user_prompt)
        itinerary_payload = self._parse_and_validate(raw_json, pois)
        self._enrich_slots_with_coordinates(itinerary_payload, pois)
        self._recompute_transit_from_slot_coordinates(itinerary_payload)

        # Persist using the first stop as the "destination" for DB compat
        dest_city = corridor["stops"][0]["city"] if corridor.get("stops") else "Road Trip"
        pseudo_location = primary_location or {
            "city": dest_city,
            "parent_region": "",
            "latitude": 0,
            "longitude": 0,
        }
        itinerary_id = self._persist(itinerary_payload, user_prefs, pseudo_location)

        stops = corridor.get("stops", [])
        first_stop = stops[0] if stops else {}

        return {
            "success": True,
            "itinerary_id": itinerary_id,
            **itinerary_payload,
            "destination": corridor["name"],
            "region": " → ".join(s["city"] for s in stops),
            "corridor_id": corridor["corridor_id"],
            "num_days": user_prefs["days"],
            "total_budget": user_prefs["budget"],
            "num_people": user_prefs.get("num_people", 1),
            "location_info": {
                "latitude": float(first_stop.get("latitude", 0)),
                "longitude": float(first_stop.get("longitude", 0)),
                "elevation": None,
                "climate_zone": None,
                "tourist_season": None,
            },
        }

    def _retrieve_corridor_pois(
        self, corridor: Dict, prefs: Dict
    ) -> List[Dict]:
        """Fetch ranked POIs for every stop on the corridor (no per-stop or total cap),
        tagged with ``route_order`` and ``_city`` so the LLM can sequence them."""
        all_pois: List[Dict] = []

        num_people = max(prefs.get("num_people", 1), 1)
        per_person_budget = prefs["budget"] / num_people
        prefs_copy = {**prefs, "budget": per_person_budget}

        for stop in corridor.get("stops", []):
            loc_id = stop.get("location_id")
            if loc_id is None:
                continue
            pois = self.db.get_pois_for_location(
                location_id=int(loc_id),
                mood_tags=prefs.get("mood"),
                activities=prefs.get("activities"),
            )
            ranked = self.matcher.filter_and_rank_pois(pois, prefs_copy)

            # Fallback: if strict filtering yields nothing, loosen threshold
            if not ranked:
                for poi in pois:
                    score = self.matcher.calculate_match_score(poi, prefs_copy)
                    if score >= 15:
                        poi["match_score"] = round(score, 2)
                        ranked.append(poi)

            # Sort POIs within this stop geographically
            self._assign_visit_order(
                ranked,
                start_lat=float(stop.get("latitude", 0)),
                start_lon=float(stop.get("longitude", 0)),
            )

            for p in ranked:
                p["route_order"] = stop["route_order"]
                p["_city"] = stop["city"]

            all_pois.extend(ranked)

        # Sort by route_order first, then by visit order within each stop
        all_pois.sort(key=lambda p: (
            p.get("route_order", 99),
            p.get("suggested_visit_order", 99),
        ))

        # Re-assign a global visit order across the whole corridor
        for idx, p in enumerate(all_pois, 1):
            p["suggested_visit_order"] = idx

        return all_pois

    @staticmethod
    def _primary_location_from_corridor(corridor: Dict) -> Optional[Dict]:
        stops = corridor.get("stops", [])
        if not stops:
            return None
        first = stops[0]
        return {
            "location_id": first.get("location_id"),
            "city": first["city"],
            "parent_region": first.get("parent_region", ""),
            "latitude": first.get("latitude", 0),
            "longitude": first.get("longitude", 0),
            "elevation": None,
            "climate_zone": None,
            "tourist_season": None,
        }

    # ------------------------------------------------------------------
    # POI retrieval (single-city)
    # ------------------------------------------------------------------

    def _retrieve_pois(self, location: Dict, prefs: Dict) -> List[Dict]:
        """Fetch and rank all POIs for a single destination (no cap)."""
        pois = self.db.get_pois_for_location(
            location_id=location["location_id"],
            mood_tags=prefs.get("mood"),
            activities=prefs.get("activities"),
        )

        num_people = max(prefs.get("num_people", 1), 1)
        per_person_budget = prefs["budget"] / num_people

        prefs_copy = {**prefs, "budget": per_person_budget}
        ranked = self.matcher.filter_and_rank_pois(pois, prefs_copy)

        if len(ranked) < prefs["days"]:
            all_pois = self.db.get_pois_for_location(location_id=location["location_id"])
            existing_ids = {p["poi_id"] for p in ranked}
            for poi in all_pois:
                if poi["poi_id"] not in existing_ids:
                    score = self.matcher.calculate_match_score(poi, prefs)
                    if score >= 15:
                        poi["match_score"] = round(score, 2)
                        ranked.append(poi)
            ranked.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        return ranked

    # ------------------------------------------------------------------
    # Geographic visit-order sorting (nearest-neighbour heuristic)
    # ------------------------------------------------------------------

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance between two points in kilometres."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1))
             * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @classmethod
    def _assign_visit_order(cls, pois: List[Dict], start_lat: float, start_lon: float) -> None:
        """Tag each POI with ``suggested_visit_order`` using the best of
        several nearest-neighbour sweeps so POIs follow a geographic path
        with no backtracking.

        Strategy:
        1. Find the two POIs that are farthest apart (the "diameter").
        2. Run nearest-neighbour from both endpoints.
        3. Pick the route whose total travel (start → first POI → … → last)
           is shortest.  This naturally produces a one-directional sweep
           for POIs spread along a road (e.g. Patriata → Murree → Nathiagali).

        Modifies *pois* **in-place** (re-sorted by visit order).
        """
        geo: List[Dict] = []
        no_geo: List[Dict] = []

        for p in pois:
            try:
                lat = float(p["latitude"])
                lon = float(p["longitude"])
                if lat == 0 and lon == 0:
                    raise ValueError
                geo.append(p)
            except (KeyError, TypeError, ValueError):
                no_geo.append(p)

        if not geo:
            for idx, p in enumerate(pois, 1):
                p["suggested_visit_order"] = idx
            return

        if len(geo) == 1:
            geo[0]["suggested_visit_order"] = 1
            for idx, p in enumerate(no_geo, 2):
                p["suggested_visit_order"] = idx
            pois.clear()
            pois.extend(geo + no_geo)
            return

        # --- find diameter (farthest pair) ---
        ep_a, ep_b = 0, 1
        best_diameter = 0.0
        for i in range(len(geo)):
            for j in range(i + 1, len(geo)):
                d = cls._haversine_km(
                    float(geo[i]["latitude"]), float(geo[i]["longitude"]),
                    float(geo[j]["latitude"]), float(geo[j]["longitude"]),
                )
                if d > best_diameter:
                    best_diameter = d
                    ep_a, ep_b = i, j

        # --- run NN from both endpoints and pick the better route ---
        route_a = cls._nn_route(geo, ep_a)
        route_b = cls._nn_route(geo, ep_b)

        cost_a = cls._route_cost(route_a, start_lat, start_lon)
        cost_b = cls._route_cost(route_b, start_lat, start_lon)

        best_route = route_a if cost_a <= cost_b else route_b

        ordered = best_route + no_geo
        for idx, p in enumerate(ordered, 1):
            p["suggested_visit_order"] = idx

        pois.clear()
        pois.extend(ordered)

    @classmethod
    def _nn_route(cls, geo: List[Dict], start_idx: int) -> List[Dict]:
        """Run nearest-neighbour starting from *geo[start_idx]*."""
        remaining = list(geo)
        first = remaining.pop(start_idx)
        route = [first]
        cur_lat = float(first["latitude"])
        cur_lon = float(first["longitude"])

        while remaining:
            best_i = 0
            best_d = float("inf")
            for i, p in enumerate(remaining):
                d = cls._haversine_km(cur_lat, cur_lon,
                                      float(p["latitude"]), float(p["longitude"]))
                if d < best_d:
                    best_d = d
                    best_i = i
            chosen = remaining.pop(best_i)
            route.append(chosen)
            cur_lat = float(chosen["latitude"])
            cur_lon = float(chosen["longitude"])

        return route

    @classmethod
    def _route_cost(cls, route: List[Dict], start_lat: float, start_lon: float) -> float:
        """Total km: start→first POI + sum of consecutive POI legs."""
        if not route:
            return 0.0
        total = cls._haversine_km(
            start_lat, start_lon,
            float(route[0]["latitude"]), float(route[0]["longitude"]),
        )
        for i in range(len(route) - 1):
            total += cls._haversine_km(
                float(route[i]["latitude"]), float(route[i]["longitude"]),
                float(route[i + 1]["latitude"]), float(route[i + 1]["longitude"]),
            )
        return total

    # ------------------------------------------------------------------
    # Hazard retrieval
    # ------------------------------------------------------------------

    def _retrieve_hazards(self, location: Dict) -> List[Dict]:
        """Fetch active NDMA hazard alerts near the destination."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'ndma_alerts_ai'
                ) AS exists
                """
            )
            if not cursor.fetchone()[0]:
                cursor.close()
                return []

            from psycopg2.extras import RealDictCursor

            cursor.close()
            cursor = self.db.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT heading, description, severity, location_name, icon_type,
                       published_date
                FROM ndma_alerts_ai
                WHERE (is_active = TRUE OR is_active IS NULL)
                  AND scraped_at >= NOW() - INTERVAL '30 days'
                ORDER BY scraped_at DESC
                LIMIT 10
                """
            )
            alerts = [dict(r) for r in cursor.fetchall()]
            cursor.close()
            return alerts
        except Exception as exc:
            logger.warning("Could not fetch NDMA hazards: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_poi_summary(self, p: Dict) -> Dict:
        """Shared POI → dict serialisation used by both prompt builders."""
        summary: Dict = {
            "poi_id": p["poi_id"],
            "name": p["name"],
            "category": p.get("category", ""),
            "description": (p.get("description") or "")[:300],
            "rating": p.get("rating"),
            "estimated_cost_pkr": p.get("estimated_cost", "0"),
            "avg_duration_hours": p.get("avg_duration_hours", 2),
            "activities": p.get("activities", ""),
            "highlights": p.get("highlights", []),
            "difficulty": p.get("difficulty", "Easy"),
            "best_months": p.get("best_months", ""),
            "latitude": p.get("latitude"),
            "longitude": p.get("longitude"),
        }
        if "suggested_visit_order" in p:
            summary["suggested_visit_order"] = p["suggested_visit_order"]
        if "route_order" in p:
            summary["route_order"] = p["route_order"]
            summary["city"] = p.get("_city", "")
        return summary

    def _build_user_prompt(
        self,
        prefs: Dict,
        pois: List[Dict],
        hazards: List[Dict],
        location: Dict,
        transit_matrix: str = "",
    ) -> str:
        """Single-city prompt."""
        poi_summaries = [self._build_poi_summary(p) for p in pois]

        hazard_block = self._format_hazards(hazards)
        transit_block = self._format_transit(transit_matrix)

        month_name = self._month_name(prefs.get("travel_month", 5))
        mood_str = ", ".join(prefs.get("mood", [])) or "general"
        activities_str = ", ".join(prefs.get("activities", [])) or "sightseeing"

        return f"""\
Plan a **{prefs['days']}-day** trip to **{location['city']}** ({location['parent_region']}).

**Traveller profile**
- Budget: PKR {prefs['budget']} total for {prefs.get('num_people', 1)} {'person' if prefs.get('num_people', 1) == 1 else 'people'}
- Mood: {mood_str}
- Preferred activities: {activities_str}
- Travel month: {month_name}
- Climate zone: {location.get('climate_zone', 'N/A')}

**IMPORTANT – Maximise the plan:**
- Fill each day with 6-10 time slots from early morning to night.
- Include Breakfast, Lunch, Dinner, Hotel Check-in/Check-out, and Rest
  slots with poi_id null where appropriate.
- Each slot must read as a concrete task: "Hiking at …", "Breakfast at …",
  "Photography at …", "Scenic Drive along …", etc.
- Use ALL relevant POIs from the list below; do not leave usable POIs out.
- **Follow the `suggested_visit_order` sequence** to avoid backtracking.
  The hotel each night must be near the last POI of that day.

<retrieved_pois>
{json.dumps(poi_summaries, indent=2, default=str)}
</retrieved_pois>
{hazard_block}{transit_block}
Generate the itinerary JSON now.
"""

    def _build_corridor_prompt(
        self,
        prefs: Dict,
        pois: List[Dict],
        hazards: List[Dict],
        corridor: Dict,
        transit_matrix: str = "",
    ) -> str:
        """Multi-city corridor prompt with route_order context."""
        poi_summaries = [self._build_poi_summary(p) for p in pois]

        hazard_block = self._format_hazards(hazards)
        transit_block = self._format_transit(transit_matrix)

        month_name = self._month_name(prefs.get("travel_month", 5))
        mood_str = ", ".join(prefs.get("mood", [])) or "general"
        activities_str = ", ".join(prefs.get("activities", [])) or "sightseeing"

        stops_desc = " → ".join(
            f"{s['city']} (order {s['route_order']})"
            for s in corridor.get("stops", [])
        )

        return f"""\
Plan a **{prefs['days']}-day multi-city road trip** along the \
**{corridor['name']}**.

**Route:** {stops_desc}
**Corridor description:** {corridor.get('description', '')}

**Traveller profile**
- Budget: PKR {prefs['budget']} total for {prefs.get('num_people', 1)} \
{'person' if prefs.get('num_people', 1) == 1 else 'people'}
- Mood: {mood_str}
- Preferred activities: {activities_str}
- Travel month: {month_name}

Each POI below has a `route_order` (which city) and a
`suggested_visit_order` (geographic sequence within and across cities).
Group POIs by `route_order` on consecutive days and within each day
follow `suggested_visit_order` to avoid backtracking.

**IMPORTANT – Maximise the plan:**
- Fill each day with 6-10 time slots from early morning to night.
- Include Breakfast, Lunch, Dinner, Hotel Check-in/Check-out, and Rest
  slots with poi_id null where appropriate.
- Each slot must read as a concrete task: "Hiking at …", "Breakfast at …",
  "Photography at …", "Scenic Drive along …", etc.
- Use ALL relevant POIs from the list below; do not leave usable POIs out.
- Long drives between cities should be their own "Scenic Drive" slot.
- **Follow the `suggested_visit_order` sequence** to avoid backtracking.
  The hotel each night must be near the last POI of that day.

<retrieved_pois>
{json.dumps(poi_summaries, indent=2, default=str)}
</retrieved_pois>
{hazard_block}{transit_block}
Generate the itinerary JSON now.
"""

    # ------------------------------------------------------------------
    # Prompt helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_hazards(hazards: List[Dict]) -> str:
        if not hazards:
            return ""
        lines = [
            f"- [{h.get('severity', 'medium').upper()}] {h.get('heading', '')} — "
            f"{h.get('description', '')} (Location: {h.get('location_name', 'N/A')})"
            for h in hazards
        ]
        return "\n<active_hazards>\n" + "\n".join(lines) + "\n</active_hazards>\n"

    @staticmethod
    def _format_transit(matrix: str) -> str:
        if not matrix:
            return ""
        return "\n<drive_time_matrix>\n" + matrix + "\n</drive_time_matrix>\n"

    @staticmethod
    def _month_name(month: int) -> str:
        names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December",
        }
        return names.get(month, "May")

    # ------------------------------------------------------------------
    # LLM call & parsing
    # ------------------------------------------------------------------

    def _call_llm(self, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=16384,
        )
        content = response.choices[0].message.content

        if response.choices[0].finish_reason == "length":
            logger.warning(
                "LLM output was truncated (finish_reason=length). "
                "Response used %s tokens.",
                response.usage.completion_tokens if response.usage else "?",
            )

        return content

    def _parse_and_validate(self, raw: str, pois: List[Dict]) -> Dict:
        """Parse the LLM JSON and do light validation."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        payload = json.loads(cleaned)

        required_top = ["itinerary_title", "trip_overview", "total_estimated_cost_pkr", "days"]
        for key in required_top:
            if key not in payload:
                raise ValueError(f"LLM output missing required key: {key}")

        if not isinstance(payload.get("days"), list):
            raise ValueError("LLM output 'days' must be a JSON array")

        valid_poi_ids = {int(p["poi_id"]) for p in pois if p.get("poi_id") is not None}
        for day in payload["days"]:
            if not isinstance(day, dict):
                continue
            for slot in day.get("time_slots", []) or []:
                if not isinstance(slot, dict):
                    continue
                pid = slot.get("poi_id")
                try:
                    pid_int = int(pid) if pid is not None and pid != "" else None
                except (TypeError, ValueError):
                    pid_int = None
                if pid_int is not None and pid_int not in valid_poi_ids:
                    logger.warning("LLM referenced unknown poi_id %s – clearing it", pid_int)
                    slot["poi_id"] = None

        self._normalize_llm_payload(payload)
        return payload

    @staticmethod
    def _normalize_llm_payload(payload: Dict) -> None:
        """Coerce LLM output into shapes the API and mobile app expect."""
        # packing_recommendations (schema: list of strings)
        pr = payload.get("packing_recommendations")
        if pr is None:
            payload["packing_recommendations"] = []
        elif isinstance(pr, list):
            payload["packing_recommendations"] = [str(x).strip() for x in pr if str(x).strip()]
        else:
            payload["packing_recommendations"] = []

        # estimated_transport_cost_pkr
        etc = payload.get("estimated_transport_cost_pkr")
        if etc is None or etc == "":
            payload["estimated_transport_cost_pkr"] = None
        else:
            try:
                payload["estimated_transport_cost_pkr"] = int(float(etc))
            except (TypeError, ValueError):
                payload["estimated_transport_cost_pkr"] = None

        # total_estimated_cost_pkr { min, max }
        tec = payload.get("total_estimated_cost_pkr")
        if isinstance(tec, (int, float)):
            v = int(tec)
            payload["total_estimated_cost_pkr"] = {"min": v, "max": v}
        elif isinstance(tec, dict):
            mn = tec.get("min", 0)
            mx = tec.get("max", mn)
            try:
                payload["total_estimated_cost_pkr"] = {
                    "min": int(float(mn)),
                    "max": int(float(mx)),
                }
            except (TypeError, ValueError):
                payload["total_estimated_cost_pkr"] = {"min": 0, "max": 0}
        else:
            payload["total_estimated_cost_pkr"] = {"min": 0, "max": 0}

        for day in payload.get("days", []):
            if not isinstance(day, dict):
                continue
            dn = day.get("day_number")
            try:
                day["day_number"] = int(dn) if dn is not None else 1
            except (TypeError, ValueError):
                day["day_number"] = 1
            day.setdefault("theme_title", f"Day {day['day_number']}")
            day.setdefault("day_summary", "")
            slots = day.get("time_slots")
            if not isinstance(slots, list):
                day["time_slots"] = []
                continue
            for slot in slots:
                if not isinstance(slot, dict):
                    continue
                pid = slot.get("poi_id")
                if pid in (None, "", "null"):
                    slot["poi_id"] = None
                else:
                    try:
                        slot["poi_id"] = int(pid)
                    except (TypeError, ValueError):
                        slot["poi_id"] = None
                ec = slot.get("estimated_cost_pkr")
                slot["estimated_cost_pkr"] = "" if ec is None else str(ec).strip() or "0"
                slot.setdefault("time_of_day", "Morning")
                slot.setdefault("start_time", "")
                slot.setdefault("end_time", "")
                slot.setdefault("activity_type", "Sightseeing")
                slot.setdefault("location_name", "")
                slot.setdefault("description", "")
                slot.setdefault("travel_tips", "")
                for key in ("transit_from_previous_mins",):
                    v = slot.get(key)
                    if v is None or v == "":
                        slot[key] = None
                    else:
                        try:
                            slot[key] = int(float(v))
                        except (TypeError, ValueError):
                            slot[key] = None
                tv = slot.get("transit_distance_km")
                if tv is None or tv == "":
                    slot["transit_distance_km"] = None
                else:
                    try:
                        slot["transit_distance_km"] = float(tv)
                    except (TypeError, ValueError):
                        slot["transit_distance_km"] = None
                ti = slot.get("transit_instruction")
                slot["transit_instruction"] = None if ti in (None, "") else str(ti)

    @staticmethod
    def _enrich_slots_with_coordinates(payload: Dict, pois: List[Dict]) -> None:
        """Attach ``latitude`` / ``longitude`` to each time slot from POI rows."""
        by_id: Dict[int, Tuple[float, float]] = {}
        for p in pois:
            pid = p.get("poi_id")
            if pid is None:
                continue
            try:
                pid_i = int(pid)
            except (TypeError, ValueError):
                continue
            try:
                lat = float(p.get("latitude"))
                lon = float(p.get("longitude"))
            except (TypeError, ValueError):
                continue
            by_id[pid_i] = (lat, lon)

        for day in payload.get("days", []) or []:
            if not isinstance(day, dict):
                continue
            for slot in day.get("time_slots", []) or []:
                if not isinstance(slot, dict):
                    continue
                pid = slot.get("poi_id")
                if pid in (None, "", "null"):
                    slot["latitude"] = None
                    slot["longitude"] = None
                    continue
                try:
                    pid_i = int(pid)
                except (TypeError, ValueError):
                    slot["latitude"] = None
                    slot["longitude"] = None
                    continue
                coords = by_id.get(pid_i)
                if coords:
                    slot["latitude"], slot["longitude"] = coords
                else:
                    slot["latitude"] = None
                    slot["longitude"] = None

    def _recompute_transit_from_slot_coordinates(self, payload: Dict) -> None:
        """Overwrite per-slot transit metrics using Geoapify (or haversine fallback).

        The LLM often emits identical ``transit_*`` values for every leg; this
        derives duration and distance from consecutive slot coordinates.
        """
        for day in payload.get("days", []) or []:
            if not isinstance(day, dict):
                continue
            slots = [s for s in (day.get("time_slots") or []) if isinstance(s, dict)]
            for i in range(1, len(slots)):
                cur = slots[i]
                prev = slots[i - 1]
                la1, lo1 = ItineraryAgent._slot_lat_lon(prev)
                la2, lo2 = ItineraryAgent._slot_lat_lon(cur)
                if None in (la1, lo1, la2, lo2):
                    continue
                if abs(la1 - la2) < 1e-8 and abs(lo1 - lo2) < 1e-8:
                    cur["transit_from_previous_mins"] = 1
                    cur["transit_distance_km"] = 0.0
                    continue
                leg = self.routing.get_drive_leg_minutes_km(la1, lo1, la2, lo2)
                if leg is not None:
                    mins, km = leg
                    cur["transit_from_previous_mins"] = int(mins)
                    cur["transit_distance_km"] = float(km)
                else:
                    km = ItineraryAgent._haversine_km(la1, lo1, la2, lo2)
                    est_min = max(5, int(round(km / 35.0 * 60)))
                    cur["transit_from_previous_mins"] = est_min
                    cur["transit_distance_km"] = round(km, 1)

    @staticmethod
    def _slot_lat_lon(slot: Dict) -> Tuple[Optional[float], Optional[float]]:
        try:
            lat = slot.get("latitude")
            lon = slot.get("longitude")
            if lat is None or lon is None:
                return None, None
            return float(lat), float(lon)
        except (TypeError, ValueError):
            return None, None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist(self, payload: Dict, prefs: Dict, location: Dict) -> int:
        """Save the generated itinerary to PostgreSQL and return its id."""
        user_id = prefs.get("user_id")
        if user_id is None or user_id == 0:
            user_id = None

        cost_range = payload.get("total_estimated_cost_pkr", {})
        total_cost = cost_range.get("max", 0) if isinstance(cost_range, dict) else 0

        itinerary_data = {
            "user_id": user_id,
            "title": payload.get("itinerary_title", "Untitled"),
            "destination": location.get("city", "Road Trip"),
            "days": prefs["days"],
            "budget": prefs["budget"],
            "season": self.matcher.get_season(prefs.get("travel_month", 5)),
            "daily_plan": payload.get("days", []),
            "total_cost": total_cost,
            "mood_tags": prefs.get("mood", []),
            "activities": prefs.get("activities", []),
            "travel_month": prefs.get("travel_month"),
        }
        return self.db.save_itinerary(itinerary_data)
