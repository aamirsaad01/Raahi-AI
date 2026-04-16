"""Context-aware chatbot service for Raahi."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from api.utils.db_helper import DatabaseHelper

repo_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
load_dotenv(dotenv_path=os.path.join(repo_root, ".env"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SNAPSHOT_TTL_MIN = 10


class ChatService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=api_key)
        self.db = DatabaseHelper()

    def close(self):
        self.db.close()

    def send_message(
        self,
        user_id: int,
        message: str,
        session_id: Optional[int] = None,
        itinerary_id: Optional[int] = None,
    ) -> Dict:
        """Send one chat message and return assistant reply."""
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        session = self._resolve_session(user_id, session_id, itinerary_id)
        sid = int(session["session_id"])

        self.db.save_chat_message(sid, user_id, "user", message)

        snapshot = self._get_or_refresh_snapshot(session, user_id, itinerary_id)
        history = self.db.get_chat_messages(sid, limit=10)
        reply = self._ask_llm(snapshot, history, message)

        self.db.save_chat_message(sid, user_id, "assistant", reply)
        self.db.touch_chat_session(sid)

        # auto-title from first user prompt
        if not session.get("title"):
            self.db.update_chat_session_title(sid, message[:140])

        return {
            "success": True,
            "session_id": sid,
            "reply": reply,
        }

    def list_sessions(self, user_id: int) -> List[Dict]:
        return self.db.get_user_chat_sessions(user_id)

    def list_messages(self, user_id: int, session_id: int) -> List[Dict]:
        session = self.db.get_chat_session(session_id)
        if not session or int(session["user_id"]) != int(user_id):
            raise ValueError("Session not found")
        return self.db.get_chat_messages(session_id, limit=500)

    # --------------------------- internals ---------------------------
    def _resolve_session(
        self,
        user_id: int,
        session_id: Optional[int],
        itinerary_id: Optional[int],
    ) -> Dict:
        if session_id is not None:
            existing = self.db.get_chat_session(session_id)
            if not existing or int(existing["user_id"]) != int(user_id):
                raise ValueError("Session not found")
            return existing
        new_id = self.db.create_chat_session(user_id=user_id, linked_itinerary_id=itinerary_id)
        created = self.db.get_chat_session(new_id)
        if not created:
            raise RuntimeError("Could not create chat session")
        return created

    def _get_or_refresh_snapshot(
        self,
        session: Dict,
        user_id: int,
        itinerary_id: Optional[int],
    ) -> Dict:
        refreshed_at = session.get("snapshot_refreshed_at")
        snapshot = session.get("context_snapshot") or {}

        should_refresh = True
        if refreshed_at and snapshot:
            try:
                if isinstance(refreshed_at, str):
                    dt = datetime.fromisoformat(refreshed_at.replace("Z", "+00:00"))
                else:
                    dt = refreshed_at
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                should_refresh = datetime.now(timezone.utc) - dt > timedelta(
                    minutes=SNAPSHOT_TTL_MIN
                )
            except Exception:
                should_refresh = True

        if not should_refresh:
            return snapshot

        new_snapshot = self._build_snapshot(
            user_id=user_id,
            itinerary_id=itinerary_id or session.get("linked_itinerary_id"),
        )
        self.db.update_chat_session_snapshot(int(session["session_id"]), new_snapshot)
        return new_snapshot

    def _build_snapshot(self, user_id: int, itinerary_id: Optional[int]) -> Dict:
        user = self.db.get_user_by_id(user_id) or {}
        user.pop("password", None)

        itinerary = None
        if itinerary_id is not None:
            itinerary = self.db.get_itinerary(int(itinerary_id))
        if itinerary is None:
            user_its = self.db.get_user_itineraries(user_id)
            itinerary = user_its[0] if user_its else None

        hazards = []
        if itinerary:
            destination = str(itinerary.get("destination", "")).strip()
            if destination:
                hazards = self.db.get_hazards_by_location_keyword(destination, limit=8)

        summary = self._summarize_itinerary(itinerary) if itinerary else {}
        return {
            "user_profile": {
                "user_id": user.get("user_id"),
                "name": user.get("name"),
                "email": user.get("email"),
                "contact_number": user.get("contact_number"),
                "dob": str(user.get("dob", "")),
                "cnic": user.get("cnic"),
                "medical_conditions": user.get("medical_conditions") or "",
            },
            "itinerary": summary,
            "hazards": hazards,
            "snapshot_generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _summarize_itinerary(itinerary: Optional[Dict]) -> Dict:
        if not itinerary:
            return {}
        daily = itinerary.get("daily_plan") or []
        top_days = daily[:3] if isinstance(daily, list) else []
        day_summaries = []
        for d in top_days:
            if isinstance(d, dict):
                day_summaries.append(
                    {
                        "day": d.get("day_number") or d.get("day"),
                        "summary": d.get("day_summary") or d.get("summary"),
                    }
                )
        return {
            "itinerary_id": itinerary.get("itinerary_id"),
            "title": itinerary.get("title") or itinerary.get("itinerary_title"),
            "destination": itinerary.get("destination"),
            "days": itinerary.get("days"),
            "budget": itinerary.get("budget"),
            "day_summaries": day_summaries,
        }

    def _ask_llm(self, snapshot: Dict, history: List[Dict], current_message: str) -> str:
        system = (
            "You are Raahi travel assistant. Reply with concise, practical guidance. "
            "Use the provided user/profile/itinerary/hazard context first. "
            "If a detail is missing, state uncertainty clearly. "
            "Prioritize safety when hazards exist."
        )

        compact_history = []
        for m in history[-8:]:
            role = m.get("role", "user")
            content = str(m.get("content", ""))
            if content:
                compact_history.append({"role": role, "content": content})

        context_block = json.dumps(snapshot, ensure_ascii=False)
        user_msg = (
            f"Context JSON:\n{context_block}\n\n"
            f"Current user question:\n{current_message}"
        )

        messages = [{"role": "system", "content": system}]
        messages.extend(compact_history)
        messages.append({"role": "user", "content": user_msg})

        resp = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=500,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or "I could not generate a response right now."

