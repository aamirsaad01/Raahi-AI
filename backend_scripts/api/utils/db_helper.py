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
        
        # Add mood filter - check if JSONB array contains any of the mood tags
        if mood_tags:
            # Build OR conditions for each mood tag
            mood_conditions = []
            for tag in mood_tags:
                mood_conditions.append("mood_tags @> %s::jsonb")
                params.append(json.dumps([tag]))
            query += f" AND ({' OR '.join(mood_conditions)})"
        
        # Add activities filter - check if JSONB array contains any of the activities
        if activities:
            # Build OR conditions for each activity
            activity_conditions = []
            for act in activities:
                activity_conditions.append("activities @> %s::jsonb")
                params.append(json.dumps([act]))
            query += f" AND ({' OR '.join(activity_conditions)})"
        
        # Add cost filter
        if max_cost:
            query += " AND estimated_cost_pkr_max <= %s"
            params.append(max_cost)
        
        # Add difficulty filter
        if difficulty:
            placeholders = ','.join(['%s'] * len(difficulty))
            query += f" AND difficulty IN ({placeholders})"
            params.extend(difficulty)
        
        query += " ORDER BY rating DESC, estimated_cost_pkr_min ASC"
        
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
        """Create new user"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (%s, %s, %s)
                RETURNING user_id
                """,
                (name, email, password)
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
        return dict(result) if result else None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

