"""
Itinerary Generator Service
Main algorithm for generating day-by-day travel itineraries
"""

import sys
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import math

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.db_helper import DatabaseHelper
from api.services.poi_matcher import POIMatcher


class ItineraryGenerator:
    """Generate personalized travel itineraries"""
    
    def __init__(self):
        """Initialize generator"""
        self.db = DatabaseHelper()
        self.matcher = POIMatcher()
    
    def generate(self, user_prefs: Dict) -> Dict:
        """
        Generate complete itinerary based on user preferences
        
        Args:
            user_prefs: Dictionary containing:
                - user_id: int
                - destination: str (city name)
                - days: int
                - budget: float (PKR)
                - mood: List[str] (e.g., ["adventurous", "romantic"])
                - activities: List[str] (e.g., ["hiking", "photography"])
                - travel_month: int (1-12)
                - start_date: str (optional, format: "YYYY-MM-DD")
        
        Returns:
            Complete itinerary dictionary
        """
        try:
            # 1. Validate and get location
            location = self.db.get_location_by_city(user_prefs['destination'])
            if not location:
                return {
                    'success': False,
                    'error': f"Location '{user_prefs['destination']}' not found",
                    'suggestion': 'Please check the spelling or try a different location'
                }
            
            # 2. Get all POIs for location
            pois = self.db.get_pois_for_location(
                location_id=location['location_id'],
                mood_tags=user_prefs.get('mood'),
                activities=user_prefs.get('activities')
            )
            
            if not pois:
                return {
                    'success': False,
                    'error': 'No attractions found for this location',
                    'suggestion': 'Try different mood/activity preferences or another destination'
                }
            
            # 3. Filter and rank POIs
            ranked_pois = self.matcher.filter_and_rank_pois(pois, user_prefs)
            
            if not ranked_pois:
                return {
                    'success': False,
                    'error': 'No attractions match your preferences',
                    'suggestion': 'Try broader mood/activity preferences'
                }
            
            # 4. Select POIs within budget
            selected_pois = self.matcher.select_pois_within_budget(
                ranked_pois,
                user_prefs['budget'],
                user_prefs['days']
            )
            
            if not selected_pois:
                return {
                    'success': False,
                    'error': 'Budget too low for any activities',
                    'suggestion': 'Increase budget or reduce number of days'
                }
            
            # 5. Create day-by-day schedule
            daily_plan = self._create_daily_schedule(
                selected_pois,
                user_prefs['days'],
                user_prefs.get('start_date')
            )
            
            # 6. Calculate costs
            cost_breakdown = self._calculate_costs(
                selected_pois,
                user_prefs['budget'],
                user_prefs['days']
            )
            
            # 7. Generate title
            title = self._generate_title(
                location['city'],
                user_prefs['days'],
                user_prefs.get('mood', [])
            )
            
            # 8. Save to database
            itinerary_data = {
                'user_id': user_prefs['user_id'],
                'title': title,
                'destination': location['city'],
                'days': user_prefs['days'],
                'budget': user_prefs['budget'],
                'season': self.matcher.get_season(user_prefs.get('travel_month', 5)),
                'daily_plan': daily_plan,
                'total_cost': cost_breakdown['total_estimated'],
                'mood_tags': user_prefs.get('mood', []),
                'activities': user_prefs.get('activities', []),
                'travel_month': user_prefs.get('travel_month')
            }
            
            itinerary_id = self.db.save_itinerary(itinerary_data)
            
            # 9. Return complete itinerary
            return {
                'success': True,
                'itinerary_id': itinerary_id,
                'title': title,
                'destination': location['city'],
                'region': location['parent_region'],
                'days': user_prefs['days'],
                'total_budget': user_prefs['budget'],
                'cost_breakdown': cost_breakdown,
                'daily_plan': daily_plan,
                'location_info': {
                    'latitude': float(location['latitude']),
                    'longitude': float(location['longitude']),
                    'elevation': float(location['elevation']) if location['elevation'] else None,
                    'climate_zone': location['climate_zone'],
                    'tourist_season': location['tourist_season']
                },
                'selected_pois_count': len(selected_pois),
                'total_pois_available': len(pois)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate itinerary: {str(e)}'
            }
    
    def _create_daily_schedule(
        self,
        pois: List[Dict],
        num_days: int,
        start_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Create day-by-day schedule
        
        Args:
            pois: Selected POIs
            num_days: Number of days
            start_date: Start date (optional)
        
        Returns:
            List of daily plans
        """
        # Parse start date
        if start_date:
            try:
                current_date = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                current_date = datetime.now()
        else:
            current_date = datetime.now()
        
        # Distribute POIs across days
        pois_per_day = math.ceil(len(pois) / num_days)
        
        daily_plan = []
        poi_index = 0
        
        for day_num in range(1, num_days + 1):
            day_pois = []
            day_cost = 0
            day_duration = 0
            
            # Aim for 6-8 hours of activities per day
            target_hours = 7
            
            # Get POIs for this day
            while poi_index < len(pois) and day_duration < target_hours:
                poi = pois[poi_index]
                poi_duration = self.matcher.estimate_time_for_poi(poi)
                
                if day_duration + poi_duration <= target_hours + 2:  # Allow 2hr overflow
                    # Calculate start time
                    start_hour = 9 + int(day_duration)  # Start at 9 AM
                    start_minute = int((day_duration % 1) * 60)
                    
                    day_pois.append({
                        'poi_id': poi['poi_id'],
                        'name': poi['name'],
                        'category': poi['category'],
                        'time': f"{start_hour:02d}:{start_minute:02d}",
                        'duration_hours': float(poi.get('avg_duration_hours', 2.0)),
                        'cost': float(poi.get('estimated_cost_pkr_max', 0)),
                        'latitude': float(poi['latitude']),
                        'longitude': float(poi['longitude']),
                        'description': poi.get('description', ''),
                        'rating': float(poi.get('rating', 0)) if poi.get('rating') else None,
                        'difficulty': poi.get('difficulty'),
                        'activities': poi.get('activities', []),
                        'highlights': poi.get('highlights', []),
                        'photos': poi.get('photos', []),
                        'match_score': poi.get('match_score', 0)
                    })
                    
                    day_cost += float(poi.get('estimated_cost_pkr_max', 0))
                    day_duration += poi_duration
                    poi_index += 1
                else:
                    # Move to next day
                    break
            
            # Add daily summary
            daily_plan.append({
                'day': day_num,
                'date': current_date.strftime("%Y-%m-%d"),
                'pois': day_pois,
                'total_duration_hours': round(day_duration, 1),
                'estimated_cost': day_cost,
                'activities_count': len(day_pois)
            })
            
            current_date += timedelta(days=1)
        
        return daily_plan
    
    def _calculate_costs(
        self,
        pois: List[Dict],
        total_budget: float,
        num_days: int
    ) -> Dict:
        """
        Calculate cost breakdown
        
        Args:
            pois: Selected POIs
            total_budget: Total budget
            num_days: Number of days
        
        Returns:
            Cost breakdown dictionary
        """
        # Convert budget to float (in case it's Decimal from database)
        total_budget = float(total_budget)
        
        # Calculate POI costs (convert to float)
        poi_costs = sum(float(poi.get('estimated_cost_pkr_max', 0)) for poi in pois)
        
        # Budget allocation
        accommodation_per_night = (total_budget * 0.40) / max(num_days - 1, 1)
        food_per_day = (total_budget * 0.20) / num_days
        transport = total_budget * 0.10
        
        accommodation_total = accommodation_per_night * max(num_days - 1, 1)
        food_total = food_per_day * num_days
        
        total_estimated = poi_costs + accommodation_total + food_total + transport
        
        return {
            'total_budget': total_budget,
            'total_estimated': round(total_estimated, 2),
            'remaining': round(total_budget - total_estimated, 2),
            'breakdown': {
                'attractions': round(poi_costs, 2),
                'accommodation': round(accommodation_total, 2),
                'food': round(food_total, 2),
                'transport': round(transport, 2)
            },
            'per_day': {
                'accommodation': round(accommodation_per_night, 2),
                'food': round(food_per_day, 2)
            }
        }
    
    def _generate_title(
        self,
        destination: str,
        days: int,
        moods: List[str]
    ) -> str:
        """Generate itinerary title"""
        mood_str = ""
        if moods:
            mood_map = {
                'adventurous': 'Adventure',
                'romantic': 'Romantic',
                'family': 'Family',
                'cultural': 'Cultural',
                'relaxed': 'Relaxing'
            }
            mood_str = mood_map.get(moods[0], moods[0].capitalize())
            mood_str = f"{mood_str} "
        
        return f"{days}-Day {mood_str}{destination} Trip"
    
    def get_itinerary(self, itinerary_id: int) -> Dict:
        """Get itinerary by ID"""
        itinerary = self.db.get_itinerary(itinerary_id)
        if not itinerary:
            return {
                'success': False,
                'error': 'Itinerary not found'
            }
        
        return {
            'success': True,
            'itinerary': itinerary
        }
    
    def get_user_itineraries(self, user_id: int) -> Dict:
        """Get all itineraries for user"""
        itineraries = self.db.get_user_itineraries(user_id)
        return {
            'success': True,
            'count': len(itineraries),
            'itineraries': itineraries
        }
    
    def update_itinerary(self, itinerary_id: int, update_data: Dict) -> Dict:
        """Update itinerary"""
        success = self.db.update_itinerary(itinerary_id, update_data)
        if success:
            return {
                'success': True,
                'message': 'Itinerary updated successfully'
            }
        return {
            'success': False,
            'error': 'Failed to update itinerary'
        }
    
    def delete_itinerary(self, itinerary_id: int) -> Dict:
        """Delete itinerary"""
        success = self.db.delete_itinerary(itinerary_id)
        if success:
            return {
                'success': True,
                'message': 'Itinerary deleted successfully'
            }
        return {
            'success': False,
            'error': 'Itinerary not found'
        }
    
    def close(self):
        """Close database connection"""
        self.db.close()

