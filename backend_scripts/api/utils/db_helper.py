"""
Database Helper Utilities
Provides database connection and query helpers
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import List, Dict, Optional
import json
from decimal import Decimal

# Load environment variables
load_dotenv()


def convert_decimals(obj):
    """Convert Decimal objects to float recursively"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


class DatabaseHelper:
    """Database connection and query helper"""
    
    def __init__(self):
        """Initialize database connection"""
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "raahi_ai"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                host=os.getenv("DB_HOST", "127.0.0.1"),
                port=os.getenv("DB_PORT", "5432"),
            )
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_location_by_city(self, city: str) -> Optional[Dict]:
        """Get location details by city name"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT * FROM location_mapping 
            WHERE LOWER(city) = LOWER(%s) AND verified = TRUE
            """,
            (city,)
        )
        result = cursor.fetchone()
        cursor.close()
        if result:
            return convert_decimals(dict(result))
        return None
    
    def get_all_locations(self) -> List[Dict]:
        """Get all verified locations"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT * FROM location_mapping 
            WHERE verified = TRUE
            ORDER BY city
            """
        )
        results = cursor.fetchall()
        cursor.close()
        locations = [dict(row) for row in results]
        return [convert_decimals(loc) for loc in locations]
    
    def get_pois_for_location(
        self,
        location_id: int,
        mood_tags: List[str] = None,
        activities: List[str] = None,
        max_cost: int = None,
        difficulty: List[str] = None
    ) -> List[Dict]:
        """
        Get POIs for a location with optional filters
        
        Args:
            location_id: Location ID
            mood_tags: Filter by mood tags (OR logic)
            activities: Filter by activities (OR logic)
            max_cost: Maximum cost in PKR
            difficulty: Filter by difficulty levels
        
        Returns:
            List of POI dictionaries
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT * FROM points_of_interest 
            WHERE location_id = %s
        """
        params = [location_id]
        
        # Add mood filter (text tags in new schema)
        if mood_tags:
            mood_conditions = []
            for tag in mood_tags:
                mood_conditions.append("(mood_tags IS NOT NULL AND LOWER(mood_tags) LIKE %s)")
                params.append(f"%{str(tag).strip().lower()}%")
            query += f" AND ({' OR '.join(mood_conditions)})"
        
        # Add activities filter (text tags in new schema)
        if activities:
            activity_conditions = []
            for act in activities:
                activity_conditions.append("(activities IS NOT NULL AND LOWER(activities) LIKE %s)")
                params.append(f"%{str(act).strip().lower()}%")
            query += f" AND ({' OR '.join(activity_conditions)})"
        
        # Add cost filter from estimated_cost text (e.g., "700 PKR")
        if max_cost:
            query += """
                AND (
                    estimated_cost IS NULL
                    OR NULLIF(REGEXP_REPLACE(estimated_cost, '[^0-9.]', '', 'g'), '')::numeric <= %s
                )
            """
            params.append(max_cost)

        # difficulty does not exist in the current table schema; ignored for compatibility

        query += " ORDER BY rating DESC NULLS LAST, poi_id ASC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        # Convert Decimal to float for all numeric fields
        pois = [dict(row) for row in results]
        return [convert_decimals(poi) for poi in pois]
    
    def save_itinerary(self, itinerary_data: Dict) -> int:
        """
        Save itinerary to database
        
        Args:
            itinerary_data: Itinerary details
        
        Returns:
            itinerary_id
        """
        cursor = self.conn.cursor()
        
        query = """
        INSERT INTO itineraries 
        (user_id, title, destination, days, budget, season, daily_plan, 
         total_cost, mood_tags, activities, travel_month)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING itinerary_id
        """
        
        cursor.execute(query, (
            itinerary_data['user_id'],
            itinerary_data['title'],
            itinerary_data['destination'],
            itinerary_data['days'],
            itinerary_data['budget'],
            itinerary_data.get('season'),
            json.dumps(itinerary_data.get('daily_plan', [])),
            itinerary_data.get('total_cost', 0),
            json.dumps(itinerary_data.get('mood_tags', [])),
            json.dumps(itinerary_data.get('activities', [])),
            itinerary_data.get('travel_month')
        ))
        
        itinerary_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        
        return itinerary_id
    
    def get_itinerary(self, itinerary_id: int) -> Optional[Dict]:
        """Get itinerary by ID"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM itineraries WHERE itinerary_id = %s",
            (itinerary_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        if result:
            return convert_decimals(dict(result))
        return None
    
    def get_user_itineraries(self, user_id: int) -> List[Dict]:
        """Get all itineraries for a user"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT * FROM itineraries 
            WHERE user_id = %s 
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        results = cursor.fetchall()
        cursor.close()
        itineraries = [dict(row) for row in results]
        return [convert_decimals(it) for it in itineraries]
    
    def update_itinerary(self, itinerary_id: int, update_data: Dict) -> bool:
        """Update itinerary"""
        cursor = self.conn.cursor()
        
        # Build dynamic update query
        set_clauses = []
        params = []
        
        allowed_fields = ['title', 'days', 'budget', 'daily_plan', 'total_cost']
        
        for field in allowed_fields:
            if field in update_data:
                set_clauses.append(f"{field} = %s")
                if field in ['daily_plan']:
                    params.append(json.dumps(update_data[field]))
                else:
                    params.append(update_data[field])
        
        if not set_clauses:
            return False
        
        params.append(itinerary_id)
        query = f"""
            UPDATE itineraries 
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE itinerary_id = %s
        """
        
        cursor.execute(query, params)
        self.conn.commit()
        cursor.close()
        
        return True
    
    def delete_itinerary(self, itinerary_id: int) -> bool:
        """Delete itinerary"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM itineraries WHERE itinerary_id = %s",
            (itinerary_id,)
        )
        self.conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0
    
    def create_user(self, name: str, email: str, password: str) -> Optional[int]:
        """Legacy helper: create minimal user row."""
        return self.create_user_profile(
            name=name,
            email=email,
            contact_number="00000000000",
            dob="1970-01-01",
            cnic=f"00000-{abs(hash(email)) % 10000000:07d}-0",
            medical_conditions="",
            password_hash=password,
            is_admin=False,
        )

    def create_user_profile(
        self,
        name: str,
        email: str,
        contact_number: str,
        dob: str,
        cnic: str,
        medical_conditions: str,
        password_hash: str,
        is_admin: bool = False,
    ) -> Optional[int]:
        """Create new user with full profile."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users
                (name, email, contact_number, dob, cnic, medical_conditions, password, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING user_id
                """,
                (
                    name,
                    email,
                    contact_number,
                    dob,
                    cnic,
                    medical_conditions,
                    password_hash,
                    is_admin,
                ),
            )
            user_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            return user_id
        except psycopg2.IntegrityError:
            # Email already exists
            self.conn.rollback()
            cursor.close()
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )
        result = cursor.fetchone()
        cursor.close()
        return convert_decimals(dict(result)) if result else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return convert_decimals(dict(result)) if result else None

    def update_user_last_login(self, user_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login_at = NOW(), updated_at = NOW() WHERE user_id = %s",
            (user_id,),
        )
        self.conn.commit()
        cursor.close()

    def get_all_users(self) -> List[Dict]:
        """Return all users for admin views."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT user_id, name, email, contact_number, dob, cnic,
                   medical_conditions, is_admin, is_active, last_login_at,
                   created_at, updated_at
            FROM users
            ORDER BY created_at DESC, user_id DESC
            """
        )
        rows = [convert_decimals(dict(r)) for r in cursor.fetchall()]
        cursor.close()
        return rows

    def update_user_profile_by_admin(self, user_id: int, update_data: Dict) -> bool:
        """Update editable user fields from admin panel."""
        cursor = self.conn.cursor()
        allowed = {
            "name",
            "email",
            "contact_number",
            "dob",
            "cnic",
            "medical_conditions",
            "is_admin",
            "is_active",
            "password",
        }
        set_clauses = []
        params = []
        for k, v in update_data.items():
            if k in allowed:
                set_clauses.append(f"{k} = %s")
                params.append(v)
        if not set_clauses:
            cursor.close()
            return False
        params.append(user_id)
        cursor.execute(
            f"""
            UPDATE users
            SET {", ".join(set_clauses)}, updated_at = NOW()
            WHERE user_id = %s
            """,
            params,
        )
        self.conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    def delete_user_and_related(self, user_id: int) -> bool:
        """Delete a user and related entities with explicit cleanup."""
        cursor = self.conn.cursor()

        # delete checklist rows tied to user's itineraries first
        cursor.execute(
            """
            DELETE FROM checklist
            WHERE itinerary_id IN (
                SELECT itinerary_id FROM itineraries WHERE user_id = %s
            )
            """,
            (user_id,),
        )

        # delete user's itineraries (even when FK is SET NULL)
        cursor.execute("DELETE FROM itineraries WHERE user_id = %s", (user_id,))

        # delete user-submitted hazards tied directly to user
        cursor.execute("DELETE FROM hazard_reports WHERE user_id = %s", (user_id,))

        # finally delete the user
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        self.conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    # ------------------------------------------------------------------
    # Chat sessions/messages
    # ------------------------------------------------------------------

    def create_chat_session(self, user_id: int, linked_itinerary_id: Optional[int] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_sessions (user_id, linked_itinerary_id, context_snapshot)
            VALUES (%s, %s, '{}'::jsonb)
            RETURNING session_id
            """,
            (user_id, linked_itinerary_id),
        )
        sid = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return sid

    def get_chat_session(self, session_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM chat_sessions WHERE session_id = %s", (session_id,))
        row = cursor.fetchone()
        cursor.close()
        return convert_decimals(dict(row)) if row else None

    def get_user_chat_sessions(self, user_id: int) -> List[Dict]:
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT session_id, user_id, linked_itinerary_id, title,
                   created_at, updated_at, last_message_at, is_archived
            FROM chat_sessions
            WHERE user_id = %s AND is_archived = FALSE
            ORDER BY last_message_at DESC, session_id DESC
            """,
            (user_id,),
        )
        rows = [convert_decimals(dict(r)) for r in cursor.fetchall()]
        cursor.close()
        return rows

    def update_chat_session_snapshot(self, session_id: int, snapshot: Dict) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE chat_sessions
            SET context_snapshot = %s::jsonb,
                snapshot_refreshed_at = NOW(),
                updated_at = NOW()
            WHERE session_id = %s
            """,
            (json.dumps(snapshot), session_id),
        )
        self.conn.commit()
        cursor.close()

    def update_chat_session_title(self, session_id: int, title: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE chat_sessions
            SET title = %s, updated_at = NOW()
            WHERE session_id = %s
            """,
            (title, session_id),
        )
        self.conn.commit()
        cursor.close()

    def touch_chat_session(self, session_id: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE chat_sessions
            SET last_message_at = NOW(), updated_at = NOW()
            WHERE session_id = %s
            """,
            (session_id,),
        )
        self.conn.commit()
        cursor.close()

    def save_chat_message(
        self,
        session_id: int,
        user_id: int,
        role: str,
        content: str,
        token_count: Optional[int] = None,
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_messages (session_id, user_id, role, content, token_count)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING message_id
            """,
            (session_id, user_id, role, content, token_count),
        )
        mid = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return mid

    def get_chat_messages(self, session_id: int, limit: int = 200) -> List[Dict]:
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT message_id, session_id, user_id, role, content, token_count, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC, message_id ASC
            LIMIT %s
            """,
            (session_id, limit),
        )
        rows = [convert_decimals(dict(r)) for r in cursor.fetchall()]
        cursor.close()
        return rows

    def get_hazards_by_location_keyword(self, location_keyword: str, limit: int = 8) -> List[Dict]:
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT hazard_id, title, description, severity, location, reported_at
            FROM hazard_reports
            WHERE location ILIKE %s
            ORDER BY reported_at DESC
            LIMIT %s
            """,
            (f"%{location_keyword}%", limit),
        )
        rows = [convert_decimals(dict(r)) for r in cursor.fetchall()]
        cursor.close()
        return rows
    
    # ------------------------------------------------------------------
    # Travel Corridors
    # ------------------------------------------------------------------

    def get_corridors_for_location(self, location_id: int) -> List[Dict]:
        """Return all corridors that pass through *location_id*,
        including their full ordered list of stops."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT tc.corridor_id, tc.name, tc.description,
                   tc.min_days, tc.base_transport_cost_pkr
            FROM travel_corridors tc
            JOIN corridor_locations cl USING (corridor_id)
            WHERE cl.location_id = %s
            ORDER BY tc.corridor_id
            """,
            (location_id,),
        )
        corridors = [convert_decimals(dict(r)) for r in cursor.fetchall()]
        cursor.close()

        for cor in corridors:
            cor["stops"] = self._get_corridor_stops(cor["corridor_id"])
        return corridors

    def get_all_corridors(self) -> List[Dict]:
        """Return every corridor with its ordered stops."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT corridor_id, name, description,
                   min_days, base_transport_cost_pkr
            FROM travel_corridors
            ORDER BY corridor_id
            """
        )
        corridors = [convert_decimals(dict(r)) for r in cursor.fetchall()]
        cursor.close()

        for cor in corridors:
            cor["stops"] = self._get_corridor_stops(cor["corridor_id"])
        return corridors

    def _get_corridor_stops(self, corridor_id: int) -> List[Dict]:
        """Ordered list of {location_id, city, route_order, …}."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT cl.route_order, lm.location_id, lm.city,
                   lm.parent_region, lm.latitude, lm.longitude
            FROM corridor_locations cl
            JOIN location_mapping lm USING (location_id)
            WHERE cl.corridor_id = %s
            ORDER BY cl.route_order
            """,
            (corridor_id,),
        )
        stops = [convert_decimals(dict(r)) for r in cursor.fetchall()]
        cursor.close()
        return stops

    def get_corridor_by_id(self, corridor_id: int) -> Optional[Dict]:
        """Fetch a single corridor with stops."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT corridor_id, name, description,
                   min_days, base_transport_cost_pkr
            FROM travel_corridors
            WHERE corridor_id = %s
            """,
            (corridor_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        cor = convert_decimals(dict(row))
        cor["stops"] = self._get_corridor_stops(corridor_id)
        return cor

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

