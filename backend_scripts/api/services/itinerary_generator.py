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
            # Get num_people (default to 1)
            num_people = user_prefs.get('num_people', 1)
            if num_people < 1:
                num_people = 1
            
            # Intelligent budget division: divide total budget by num_people for per-person calculations
            total_budget = user_prefs['budget']
            per_person_budget = total_budget / num_people
            
            # Update user_prefs with per-person budget for matching/selection
            user_prefs_for_matching = user_prefs.copy()
            user_prefs_for_matching['budget'] = per_person_budget
            user_prefs_for_matching['num_people'] = num_people
            
            # 1. Validate and get location
            location = self.db.get_location_by_city(user_prefs['destination'])
            if not location:
                return {
                    'success': False,
                    'error': f"Location '{user_prefs['destination']}' not found",
                    'suggestion': 'Please check the spelling or try a different location'
                }
            
            # 2. Get all POIs for location (with filters)
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
            
            # 3. Filter and rank POIs (using per-person budget for matching)
            ranked_pois = self.matcher.filter_and_rank_pois(pois, user_prefs_for_matching)
            
            # Solution 4: Fallback POIs - if not enough match filters, include general POIs
            min_pois_needed = user_prefs['days']  # At least 1 POI per day
            if len(ranked_pois) < min_pois_needed:
                # Get all POIs without filters as fallback
                all_pois = self.db.get_pois_for_location(
                    location_id=location['location_id'],
                    mood_tags=None,
                    activities=None
                )
                
                # Score all POIs and add those not already in ranked_pois
                existing_poi_ids = {poi['poi_id'] for poi in ranked_pois}
                for poi in all_pois:
                    if poi['poi_id'] not in existing_poi_ids:
                        score = self.matcher.calculate_match_score(poi, user_prefs)
                        if score >= 20:  # Lower threshold for fallback (20% match)
                            poi_copy = poi.copy()
                            poi_copy['match_score'] = round(score, 2)
                            ranked_pois.append(poi_copy)
                
                # Re-sort by match score
                ranked_pois.sort(key=lambda x: x['match_score'], reverse=True)
            
            if not ranked_pois:
                return {
                    'success': False,
                    'error': 'No attractions match your preferences',
                    'suggestion': 'Try broader mood/activity preferences'
                }
            
            # 4. Select POIs within budget (ensures minimum POIs per day, using per-person budget)
            selected_pois = self.matcher.select_pois_within_budget(
                ranked_pois,
                per_person_budget,
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
            
            # 6. Calculate costs (using total budget and num_people for scaling)
            cost_breakdown = self._calculate_costs(
                selected_pois,
                total_budget,
                user_prefs['days'],
                num_people
            )
            
            # 7. Generate title
            title = self._generate_title(
                location['city'],
                user_prefs['days'],
                user_prefs.get('mood', [])
            )
            
            # 8. Save to database
            # user_id is optional (NULL for anonymous users)
            user_id = user_prefs.get('user_id')
            if user_id is None or user_id == 0:
                user_id = None  # Use NULL for anonymous users
            
            itinerary_data = {
                'user_id': user_id,
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
                'total_budget': total_budget,
                'num_people': num_people,
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
        Solution 1 & 2: Ensures minimum 1 POI per day and even distribution
        
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
        
        # Solution 2: Even distribution - distribute POIs evenly across all days first
        # Calculate base POIs per day
        base_pois_per_day = len(pois) // num_days
        extra_pois = len(pois) % num_days  # Remaining POIs to distribute
        
        # Create a list of POI indices for each day
        day_poi_indices = []
        poi_index = 0
        
        for day_num in range(num_days):
            # Each day gets base_pois_per_day, some days get one extra
            pois_for_day = base_pois_per_day + (1 if day_num < extra_pois else 0)
            day_indices = list(range(poi_index, poi_index + pois_for_day))
            day_poi_indices.append(day_indices)
            poi_index += pois_for_day
        
        daily_plan = []
        
        for day_num in range(1, num_days + 1):
            day_pois = []
            day_cost = 0
            day_duration = 0
            
            # Solution 1: Minimum 1 POI per day - get POIs assigned to this day
            day_indices = day_poi_indices[day_num - 1]
            
            # Aim for 6-8 hours of activities per day
            target_hours = 7
            
            # Process POIs assigned to this day
            for idx in day_indices:
                if idx >= len(pois):
                    break
                    
                poi = pois[idx]
                poi_duration = self.matcher.estimate_time_for_poi(poi)
                
                # Allow POI even if it slightly exceeds target (ensures at least 1 per day)
                if day_duration + poi_duration <= target_hours + 3 or len(day_pois) == 0:
                    # Calculate start time
                    start_hour = 9 + int(day_duration)  # Start at 9 AM
                    start_minute = int((day_duration % 1) * 60)
                    
                    # Get per-person cost
                    per_person_poi_cost = float(poi.get('estimated_cost_pkr_max', 0))
                    
                    day_pois.append({
                        'poi_id': poi['poi_id'],
                        'name': poi['name'],
                        'category': poi['category'],
                        'time': f"{start_hour:02d}:{start_minute:02d}",
                        'duration_hours': float(poi.get('avg_duration_hours', 2.0)),
                        'cost': per_person_poi_cost,  # Per-person cost
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
                    
                    day_cost += per_person_poi_cost  # This will be scaled later in cost calculation
                    day_duration += poi_duration
            
            # Solution 1: Ensure at least 1 POI per day (should already be guaranteed by distribution)
            if len(day_pois) == 0 and len(pois) > 0:
                # Fallback: if somehow no POI assigned, take the first available
                # This should not happen with even distribution, but safety check
                remaining_poi = pois[min(day_num - 1, len(pois) - 1)]
                poi_duration = self.matcher.estimate_time_for_poi(remaining_poi)
                
                day_pois.append({
                    'poi_id': remaining_poi['poi_id'],
                    'name': remaining_poi['name'],
                    'category': remaining_poi['category'],
                    'time': "09:00",
                    'duration_hours': float(remaining_poi.get('avg_duration_hours', 2.0)),
                    'cost': float(remaining_poi.get('estimated_cost_pkr_max', 0)),
                    'latitude': float(remaining_poi['latitude']),
                    'longitude': float(remaining_poi['longitude']),
                    'description': remaining_poi.get('description', ''),
                    'rating': float(remaining_poi.get('rating', 0)) if remaining_poi.get('rating') else None,
                    'difficulty': remaining_poi.get('difficulty'),
                    'activities': remaining_poi.get('activities', []),
                    'highlights': remaining_poi.get('highlights', []),
                    'photos': remaining_poi.get('photos', []),
                    'match_score': remaining_poi.get('match_score', 0)
                })
                day_cost = float(remaining_poi.get('estimated_cost_pkr_max', 0))
                day_duration = poi_duration
            
            # Add daily summary
            daily_plan.append({
                'day': day_num,
                'date': current_date.strftime("%Y-%m-%d"),
                'pois': day_pois,
                'total_duration_hours': round(day_duration, 1),
                'estimated_cost': day_cost,
                'activities_count': len(day_pois),
                'summary': self._generate_day_summary(day_pois)
            })
            
            current_date += timedelta(days=1)
        
        return daily_plan
    
    def _generate_day_summary(self, day_pois: List[Dict]) -> str:
        """Generate a brief summary for the day"""
        if not day_pois:
            return "Free day - explore at your own pace"
        
        poi_names = [poi['name'] for poi in day_pois]
        if len(poi_names) == 1:
            return f"Visit {poi_names[0]}"
        elif len(poi_names) == 2:
            return f"Visit {poi_names[0]} and {poi_names[1]}"
        else:
            return f"Visit {', '.join(poi_names[:-1])}, and {poi_names[-1]}"
    
    def _calculate_costs(
        self,
        pois: List[Dict],
        total_budget: float,
        num_days: int,
        num_people: int = 1
    ) -> Dict:
        """
        Calculate cost breakdown with intelligent scaling for number of people
        
        Args:
            pois: Selected POIs (per-person costs)
            total_budget: Total budget for all people
            num_days: Number of days
            num_people: Number of people
        
        Returns:
            Cost breakdown dictionary with total and per-person costs
        """
        # Convert budget to float (in case it's Decimal from database)
        total_budget = float(total_budget)
        num_people = max(1, int(num_people))  # Ensure at least 1 person
        
        # Calculate per-person budget
        per_person_budget = total_budget / num_people
        
        # POI costs: Entry fees scale linearly with num_people
        per_person_poi_cost = sum(float(poi.get('estimated_cost_pkr_max', 0)) for poi in pois)
        total_poi_costs = per_person_poi_cost * num_people
        
        # Budget allocation (per person, then scale)
        per_person_accommodation_per_night = (per_person_budget * 0.40) / max(num_days - 1, 1)
        per_person_food_per_day = (per_person_budget * 0.20) / num_days
        per_person_transport = per_person_budget * 0.10
        
        # Scale to total for all people
        accommodation_per_night = per_person_accommodation_per_night * num_people
        food_per_day = per_person_food_per_day * num_people
        transport = per_person_transport * num_people
        
        accommodation_total = accommodation_per_night * max(num_days - 1, 1)
        food_total = food_per_day * num_days
        
        total_estimated = total_poi_costs + accommodation_total + food_total + transport
        
        return {
            'total_budget': total_budget,
            'total_estimated': round(total_estimated, 2),
            'remaining': round(total_budget - total_estimated, 2),
            'num_people': num_people,
            'per_person_budget': round(per_person_budget, 2),
            'per_person_estimated': round(total_estimated / num_people, 2),
            'breakdown': {
                'attractions': round(total_poi_costs, 2),
                'accommodation': round(accommodation_total, 2),
                'food': round(food_total, 2),
                'transport': round(transport, 2)
            },
            'per_day': {
                'accommodation': round(accommodation_per_night, 2),
                'food': round(food_per_day, 2)
            },
            'per_person_breakdown': {
                'attractions': round(per_person_poi_cost, 2),
                'accommodation': round(accommodation_total / num_people, 2),
                'food': round(food_total / num_people, 2),
                'transport': round(transport / num_people, 2)
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

