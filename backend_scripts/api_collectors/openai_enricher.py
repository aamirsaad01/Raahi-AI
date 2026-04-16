"""
POI enrichment via OpenAI Chat Completions (paid API).
Uses OSM-sourced POI fields as grounding context; returns the same shape as Ollama enricher.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from api_collectors.poi_enrichment_common import (
    build_enrichment_prompt,
    default_enrichment,
    normalize_enriched_dict,
    parse_enrichment_response,
)

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a Pakistani tourism expert. Respond with a single JSON object only. "
    "No markdown fences, no commentary. All required fields from the user schema must be present."
)


class OpenAIPOIEnricher:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 4,
    ):
        key = api_key or os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Add it to your project root .env file."
            )

        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "The 'openai' package is required. Install with: pip install openai"
            ) from e

        self._client = OpenAI(api_key=key, timeout=timeout)
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self._max_retries = max_retries
        logger.info("OpenAI POI enricher ready (model=%s)", self._model)

    def enrich_poi(self, poi_data: Dict[str, Any]) -> Dict[str, Any]:
        poi_name = poi_data.get("name", "Unknown")
        location = poi_data.get("location_name", "Pakistan")
        category = poi_data.get("category", "nature")
        initial_activities = poi_data.get("activities") or []
        osm_tags = poi_data.get("osm_tags") or {}

        user_prompt = build_enrichment_prompt(
            poi_name, location, category, initial_activities, osm_tags
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_prompt
                + "\n\nReturn one JSON object matching the schema described above.",
            },
        ]

        last_err: Optional[Exception] = None
        for attempt in range(self._max_retries):
            try:
                logger.info("OpenAI enriching: %s (%s)", poi_name, location)
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                content = (resp.choices[0].message.content or "").strip()
                if not content:
                    raise ValueError("Empty completion content")

                raw = parse_enrichment_response(content)
                normalized = normalize_enriched_dict(raw, category)
                logger.info("OpenAI enriched: %s", poi_name)
                return normalized

            except Exception as e:
                last_err = e
                wait = min(2**attempt, 30)
                logger.warning(
                    "OpenAI attempt %d/%d failed for %s: %s — retry in %ds",
                    attempt + 1,
                    self._max_retries,
                    poi_name,
                    e,
                    wait,
                )
                time.sleep(wait)

        logger.error("OpenAI enrichment failed for %s: %s", poi_name, last_err)
        return normalize_enriched_dict(
            default_enrichment(poi_name, category), category
        )
