"""
Itinerary Recommender Service
Recommends destinations using a three-tier cascading strategy:
  L1 – Multi-city corridor (road-trip) if budget & days allow
  L2 – Single-city hub fallback
  L3 – Graceful rejection when budget is mathematically impossible
"""

import logging
import sys
import os
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.db_helper import DatabaseHelper
from api.services.poi_matcher import POIMatcher, parse_estimated_cost_pkr, _split_tag_text

logger = logging.getLogger(__name__)

# Rough per-person daily minimums in PKR (food + basic stay)
_MIN_DAILY_COST_PKR = 3000


class ItineraryRecommender:
    """Recommend destination options based on budget and mood."""

    def __init__(self):
        self.db = DatabaseHelper()
        self.matcher = POIMatcher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend_destinations(
        self,
        budget: float,
        mood: List[str],
        activities: List[str] = None,
        days: int = 3,
        travel_month: int = 5,
        num_recommendations: int = 5,
        num_people: int = 1,
    ) -> Dict:
        """Three-tier cascading recommendation.

        Returns a dict with ``success``, ``tier`` (1/2/3), and
        either ``recommendations`` or ``error`` + ``suggestion``.
        """
        try:
            per_person_budget = budget / max(num_people, 1)
            min_viable = _MIN_DAILY_COST_PKR * days

            # ── LEVEL 3: Graceful rejection ──────────────────────
            if per_person_budget < min_viable:
                suggested_budget = min_viable * num_people
                return {
                    "success": False,
                    "tier": 3,
                    "error": (
                        f"A budget of PKR {int(budget)} for {num_people} "
                        f"{'person' if num_people == 1 else 'people'} over "
                        f"{days} days is too low for any destination."
                    ),
                    "suggestion": (
                        f"Increase to at least PKR {int(suggested_budget)} "
                        f"or reduce the trip to {max(1, int(per_person_budget // _MIN_DAILY_COST_PKR))} days."
                    ),
                }

            user_prefs = {
                "budget": per_person_budget,
                "mood": mood,
                "activities": activities or [],
                "days": days,
                "travel_month": travel_month,
                "num_people": num_people,
            }

            # ── LEVEL 1: Corridor (multi-city road trip) ─────────
            corridor_recs = self._score_corridors(
                user_prefs, budget, per_person_budget, days, num_people, travel_month
            )

            # ── LEVEL 2: Single-city hub ─────────────────────────
            hub_recs = self._score_single_cities(
                user_prefs, budget, per_person_budget, days, num_people, mood, activities, travel_month
            )

            # Merge both tiers, sort by score, and return top N
            all_recs = corridor_recs + hub_recs
            if not all_recs:
                return {
                    "success": False,
                    "tier": 2,
                    "error": "No destinations match your preferences.",
                    "suggestion": "Try increasing budget or broader mood preferences.",
                }

            all_recs.sort(key=lambda r: r["match_score"], reverse=True)
            top = all_recs[:num_recommendations]

            for idx, rec in enumerate(top, 1):
                rec["rank"] = idx

            tier = 1 if any(r.get("type") == "corridor" for r in top) else 2

            return {
                "success": True,
                "tier": tier,
                "count": len(top),
                "recommendations": top,
                "search_criteria": {
                    "budget": budget,
                    "mood": mood,
                    "activities": activities or [],
                    "days": days,
                    "travel_month": travel_month,
                },
            }

        except Exception as exc:
            logger.exception("recommend_destinations failed")
            return {
                "success": False,
                "error": f"Failed to generate recommendations: {exc}",
            }

    def close(self):
        self.db.close()

    # ------------------------------------------------------------------
    # LEVEL 1 – Corridor scoring
    # ------------------------------------------------------------------

    def _score_corridors(
        self,
        user_prefs: Dict,
        total_budget: float,
        per_person_budget: float,
        days: int,
        num_people: int,
        travel_month: int,
    ) -> List[Dict]:
        """Score every corridor and return those that are affordable."""
        try:
            corridors = self.db.get_all_corridors()
        except Exception:
            logger.debug("travel_corridors table may not exist yet")
            return []

        results: List[Dict] = []
        for cor in corridors:
            if days < cor["min_days"]:
                continue

            transport_cost = cor["base_transport_cost_pkr"]
            min_stay_cost = _MIN_DAILY_COST_PKR * days * num_people
            if total_budget < transport_cost + min_stay_cost:
                continue

            # Collect POIs across all corridor stops
            all_pois: List[Dict] = []
            for stop in cor.get("stops", []):
                pois = self.db.get_pois_for_location(
                    location_id=stop["location_id"],
                    mood_tags=user_prefs.get("mood"),
                    activities=user_prefs.get("activities"),
                )
                ranked = self.matcher.filter_and_rank_pois(pois, user_prefs)
                for p in ranked:
                    p["_route_order"] = stop["route_order"]
                    p["_city"] = stop["city"]
                all_pois.extend(ranked)

            if not all_pois:
                continue

            avg_score = sum(p.get("match_score", 0) for p in all_pois) / len(all_pois)
            # Corridors get a bonus for offering a richer experience
            corridor_bonus = min(15, len(cor.get("stops", [])) * 3)
            final_score = min(100, (avg_score / 100) * 60 + 20 + corridor_bonus)

            stops_preview = [s["city"] for s in cor.get("stops", [])]

            top_pois = sorted(all_pois, key=lambda p: p.get("match_score", 0), reverse=True)[:5]
            preview_photos = self._extract_photos(top_pois, stops_preview[0] if stops_preview else "Pakistan")

            unique_activities = list(
                {a for p in all_pois for a in (p.get("activities") or []) if isinstance(a, str)}
            )[:5]

            results.append({
                "type": "corridor",
                "rank": 0,
                "destination": cor["name"],
                "region": " → ".join(stops_preview),
                "corridor_id": cor["corridor_id"],
                "match_score": round(final_score, 2),
                "preview": {
                    "title": f"{days}-Day {cor['name']}",
                    "photos": preview_photos,
                    "highlights": [p["name"] for p in top_pois[:3]],
                    "activities": unique_activities,
                    "cost_estimate": {
                        "total_budget": total_budget,
                        "transport": transport_cost,
                        "within_budget": True,
                    },
                    "poi_count": len(all_pois),
                    "stops": stops_preview,
                    "min_days": cor["min_days"],
                },
            })

        return results

    # ------------------------------------------------------------------
    # LEVEL 2 – Single-city hub scoring (original logic)
    # ------------------------------------------------------------------

    def _score_single_cities(
        self,
        user_prefs: Dict,
        total_budget: float,
        per_person_budget: float,
        days: int,
        num_people: int,
        mood: List[str],
        activities: List[str] | None,
        travel_month: int,
    ) -> List[Dict]:
        locations = self.db.get_all_locations()
        results: List[Dict] = []

        for location in locations:
            pois = self.db.get_pois_for_location(
                location_id=location["location_id"],
                mood_tags=mood,
                activities=activities,
            )
            if not pois:
                continue

            ranked = self.matcher.filter_and_rank_pois(pois, user_prefs)
            if not ranked:
                continue

            selected = self.matcher.select_pois_within_budget(ranked, per_person_budget, days)
            if not selected:
                continue

            score = self._calculate_location_score(location, selected, per_person_budget, days, travel_month)
            preview = self._create_preview(location, selected, total_budget, days, num_people)

            results.append({
                "type": "hub",
                "rank": 0,
                "destination": location["city"],
                "region": location["parent_region"],
                "location_id": location["location_id"],
                "match_score": round(score, 2),
                "preview": preview,
            })

        return results

    # ------------------------------------------------------------------
    # Scoring & preview helpers (unchanged from original)
    # ------------------------------------------------------------------

    def _calculate_location_score(
        self,
        location: Dict,
        pois: List[Dict],
        budget: float,
        days: int,
        travel_month: int,
    ) -> float:
        score = 0.0

        if pois:
            avg_poi_score = sum(poi.get("match_score", 0) for poi in pois) / len(pois)
            score += (avg_poi_score / 100) * 40

        poi_count = len(pois)
        if poi_count >= days * 3:
            score += 20
        elif poi_count >= days * 2:
            score += 15
        elif poi_count >= days:
            score += 10

        total_poi_cost = sum(parse_estimated_cost_pkr(poi) for poi in pois)
        poi_budget = budget * 0.30
        if total_poi_cost <= poi_budget:
            score += 20
        elif total_poi_cost <= poi_budget * 1.2:
            score += 15
        elif total_poi_cost <= poi_budget * 1.5:
            score += 10

        tourist_season = location.get("tourist_season") or ""
        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        if 1 <= travel_month <= 12:
            if month_names[travel_month] in tourist_season:
                score += 10
            else:
                score += 5

        unique_categories = {poi.get("category") for poi in pois}
        if len(unique_categories) >= 3:
            score += 10
        elif len(unique_categories) >= 2:
            score += 7
        else:
            score += 3

        return min(score, 100)

    def _create_preview(
        self,
        location: Dict,
        pois: List[Dict],
        budget: float,
        days: int,
        num_people: int = 1,
    ) -> Dict:
        per_person_poi_cost = sum(parse_estimated_cost_pkr(poi) for poi in pois)
        total_poi_cost = per_person_poi_cost * num_people

        per_person_budget = budget / num_people
        accommodation_cost = (per_person_budget * 0.40) * num_people
        food_cost = (per_person_budget * 0.20) * num_people
        transport_cost = (per_person_budget * 0.10) * num_people

        total_estimated = total_poi_cost + accommodation_cost + food_cost + transport_cost

        top_pois = pois[:3]
        preview_photos = self._extract_photos(top_pois, location["city"])

        all_activities: List[str] = []
        for poi in pois:
            all_activities.extend(_split_tag_text(poi.get("activities")))
        unique_activities = list(dict.fromkeys(all_activities))[:5]

        categories = list({poi.get("category") for poi in pois if poi.get("category")})

        return {
            "title": f"{days}-Day {location['city']} Adventure",
            "destination": location["city"],
            "region": location["parent_region"],
            "days": days,
            "photos": preview_photos,
            "highlights": [poi["name"] for poi in top_pois],
            "activities": unique_activities,
            "categories": categories,
            "cost_estimate": {
                "total_budget": budget,
                "estimated_cost": round(total_estimated, 2),
                "within_budget": total_estimated <= budget,
                "breakdown": {
                    "attractions": round(total_poi_cost, 2),
                    "accommodation": round(accommodation_cost, 2),
                    "food": round(food_cost, 2),
                    "transport": round(transport_cost, 2),
                },
            },
            "poi_count": len(pois),
            "average_rating": round(
                sum(poi.get("rating", 0) for poi in pois if poi.get("rating"))
                / len([p for p in pois if p.get("rating")]),
                1,
            )
            if any(poi.get("rating") for poi in pois)
            else None,
            "location_info": {
                "latitude": float(location["latitude"]),
                "longitude": float(location["longitude"]),
                "elevation": float(location["elevation"]) if location.get("elevation") else None,
                "climate_zone": location.get("climate_zone"),
                "tourist_season": location.get("tourist_season"),
            },
        }

    @staticmethod
    def _extract_photos(pois: List[Dict], fallback_city: str) -> List[Dict]:
        preview_photos: List[Dict] = []
        for poi in pois:
            photos = poi.get("photos", [])
            if photos and isinstance(photos, list) and len(photos) > 0:
                preview_photos.append({
                    "poi_name": poi["name"],
                    "photo": photos[0],
                    "rating": float(poi.get("rating", 0)) if poi.get("rating") else None,
                })
        if not preview_photos:
            preview_photos = [{
                "poi_name": fallback_city,
                "photo": {
                    "url": f"https://source.unsplash.com/800x600/?{fallback_city},pakistan,travel",
                    "photographer": "Unsplash",
                },
                "rating": None,
            }]
        return preview_photos[:4]
