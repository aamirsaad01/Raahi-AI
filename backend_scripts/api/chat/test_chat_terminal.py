"""Quick terminal chat tester using existing DB user + itinerary.

Usage:
  python test_chat_terminal.py
  python test_chat_terminal.py --user-id 3 --itinerary-id 12
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.chat.service import ChatService
from api.utils.db_helper import DatabaseHelper


def pick_default_user_and_itinerary(db: DatabaseHelper) -> tuple[Optional[int], Optional[int]]:
    users = db.get_all_users()
    if not users:
        return None, None

    user = None
    for u in users:
        if not u.get("is_admin"):
            user = u
            break
    if user is None:
        user = users[0]

    uid = int(user["user_id"])
    its = db.get_user_itineraries(uid)
    iid = int(its[0]["itinerary_id"]) if its else None
    return uid, iid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--itinerary-id", type=int, default=None)
    args = parser.parse_args()

    db = DatabaseHelper()
    try:
        user_id = args.user_id
        itinerary_id = args.itinerary_id
        if user_id is None:
            picked_uid, picked_iid = pick_default_user_and_itinerary(db)
            user_id = picked_uid
            if itinerary_id is None:
                itinerary_id = picked_iid
    finally:
        db.close()

    if user_id is None:
        print("No users found in DB. Create a user first.")
        return

    print("=" * 70)
    print(f"Chat test started with user_id={user_id}, itinerary_id={itinerary_id}")
    print("Type 'exit' to quit.")
    print("=" * 70)

    service = ChatService()
    session_id = None
    try:
        while True:
            q = input("\nYou: ").strip()
            if not q:
                continue
            if q.lower() in {"exit", "quit"}:
                break
            out = service.send_message(
                user_id=user_id,
                message=q,
                session_id=session_id,
                itinerary_id=itinerary_id,
            )
            session_id = out.get("session_id", session_id)
            print(f"\nRaahi [{session_id}]: {out.get('reply', '')}\n")
    finally:
        service.close()


if __name__ == "__main__":
    main()

