#!/usr/bin/env python3
"""
Runnable unit-style checks for itinerary-related flows.

Run from repo root (recommended):
    python backend_scripts/unit_test_cases/itnerary_test_cases.py

Or from backend_scripts:
    python unit_test_cases/itnerary_test_cases.py

Requires: .env with DB_* (and OPENAI_API_KEY only for hazard/agent tests that use ItineraryAgent).
"""

from __future__ import annotations

import os
import sys
import unittest

# backend_scripts on path so `import api...` works (same pattern as api/services)
_BACKEND_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_SCRIPTS)

_REPO_ROOT = os.path.dirname(_BACKEND_SCRIPTS)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(dotenv_path=os.path.join(_REPO_ROOT, ".env"))


class TestItineraryBudget(unittest.TestCase):
    """Category 1: budget constraint (recommender tier-3 rejection)."""

    def test_recommender_rejects_impossible_budget(self) -> None:
        """Per-person budget below minimum daily floor × days → success False, tier 3."""
        from api.services.itinerary_recommender import ItineraryRecommender

        rec = ItineraryRecommender()
        try:
            result = rec.recommend_destinations(
                budget=500,
                mood=["adventurous"],
                activities=["hiking"],
                days=7,
                travel_month=6,
                num_recommendations=3,
                num_people=1,
            )
            self.assertFalse(result.get("success"), msg=result)
            self.assertEqual(result.get("tier"), 3)
            self.assertIn("error", result)
            self.assertIn("suggestion", result)
            print(f"   error: {result['error'][:120]}...")
        finally:
            rec.close()


class TestItineraryUnknownCity(unittest.TestCase):
    """Category 2: destination not in location_mapping."""

    def test_generator_rejects_unknown_city(self) -> None:
        """Legacy generator must not return an itinerary for a fake city."""
        from api.services.itinerary_generator import ItineraryGenerator

        gen = ItineraryGenerator()
        try:
            result = gen.generate(
                {
                    "user_id": None,
                    "destination": "__NONEXISTENT_CITY_XYZ__",
                    "days": 3,
                    "budget": 200_000,
                    "mood": ["adventurous"],
                    "activities": ["hiking"],
                    "travel_month": 6,
                    "num_people": 1,
                }
            )
            self.assertFalse(result.get("success"), msg=result)
            self.assertIn("error", result)
            print(f"   error: {result['error']}")
        finally:
            gen.close()

    def test_agent_terminal_unknown_city_when_configured(self) -> None:
        """RAG agent returns terminal failure for unknown city (no fallback in API)."""
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set – skipping ItineraryAgent test")

        from api.services.itinerary_agent import ItineraryAgent

        agent = ItineraryAgent()
        try:
            result = agent.generate(
                {
                    "destination": "__NONEXISTENT_CITY_XYZ__",
                    "days": 3,
                    "budget": 200_000,
                    "mood": ["adventurous"],
                    "activities": ["hiking"],
                    "travel_month": 6,
                    "num_people": 1,
                }
            )
            self.assertFalse(result.get("success"), msg=result)
            self.assertTrue(result.get("terminal"), msg=result)
            self.assertIn("not in our database", result.get("error", "").lower())
            print(f"   error: {result['error']}")
        finally:
            agent.close()


class TestItineraryHazards(unittest.TestCase):
    """Category 3: hazard context for itinerary (NDMA → agent pipeline)."""

    def test_ndma_active_alerts_query_runs(self) -> None:
        """DB layer: active-recent NDMA query is valid (may return 0 rows)."""
        from api.utils.db_helper import DatabaseHelper

        db = DatabaseHelper()
        try:
            cur = db.conn.cursor()
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'ndma_alerts_ai'
                )
                """
            )
            exists = cur.fetchone()[0]
            cur.close()
            if not exists:
                self.skipTest("Table ndma_alerts_ai not present")

            cur = db.conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*)
                FROM ndma_alerts_ai
                WHERE (is_active = TRUE OR is_active IS NULL)
                  AND scraped_at >= NOW() - INTERVAL '30 days'
                """
            )
            count = cur.fetchone()[0]
            cur.close()
            print(f"   Active/recent NDMA rows (30d): {count}")
            self.assertIsInstance(count, int)
        finally:
            db.close()

    def test_agent_retrieve_hazards_returns_list(self) -> None:
        """ItineraryAgent._retrieve_hazards must return a list (feeds LLM prompt when alerts exist)."""
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set – skipping ItineraryAgent test")

        from api.services.itinerary_agent import ItineraryAgent

        agent = ItineraryAgent()
        try:
            cur = agent.db.conn.cursor()
            cur.execute(
                "SELECT city FROM location_mapping ORDER BY city ASC LIMIT 1"
            )
            row = cur.fetchone()
            cur.close()
            if not row:
                self.skipTest("No rows in location_mapping")

            city = row[0]
            location = agent.db.get_location_by_city(city)
            self.assertIsNotNone(location)

            hazards = agent._retrieve_hazards(location)
            self.assertIsInstance(hazards, list)
            print(f"   Sample city: {city} | hazards in prompt context: {len(hazards)}")
        finally:
            agent.close()


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestItineraryBudget))
    suite.addTests(loader.loadTestsFromTestCase(TestItineraryUnknownCity))
    suite.addTests(loader.loadTestsFromTestCase(TestItineraryHazards))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print()
    print("=" * 60)
    print(f"Ran {result.testsRun} tests | failures={len(result.failures)} | errors={len(result.errors)}")
    print("=" * 60)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
