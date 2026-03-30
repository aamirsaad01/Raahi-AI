"""
Itinerary Recommender Service
Recommends multiple destination options based on user preferences
"""

import sys
import os
from typing import List, Dict
import random

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.utils.db_helper import DatabaseHelper
from api.services.poi_matcher import POIMatcher


class ItineraryRecommender:
    """Recommend destination options based on budget and mood"""
    
    def __init__(self):
        """Initialize recommender"""
        self.db = DatabaseHelper()
        self.matcher = POIMatcher()
    
    def recommend_destinations(
        self,
        budget: float,
        mood: List[str],
        activities: List[str] = None,
        days: int = 3,
        travel_month: int = 5,
        num_recommendations: int = 5,
        num_people: int = 1
    ) -> Dict:
        """
        Recommend multiple destination options
        
        Args:
            budget: Total budget in PKR
            mood: List of mood tags (e.g., ["adventurous", "romantic"])
            activities: Optional list of activities
            days: Number of days
            travel_month: Month of travel (1-12)
            num_recommendations: Number of destinations to recommend
        
        Returns:
            Dictionary with recommendations
        """
        try:
            # Get all locations from database
            locations = self.db.get_all_locations()
            
            if not locations:
                return {
                    'success': False,
                    'error': 'No locations available'
                }
            
            # Score each location
            scored_locations = []
            
            for location in locations:
                # Get POIs for this location
                pois = self.db.get_pois_for_location(
                    location_id=location['location_id'],
                    mood_tags=mood,
                    activities=activities
                )
                
                if not pois:
                    continue
                
                # Intelligent budget division: divide total budget by num_people for per-person calculations
                per_person_budget = budget / num_people
                
                # Calculate user preferences dict (use per-person budget for matching)
                user_prefs = {
                    'budget': per_person_budget,
                    'mood': mood,
                    'activities': activities or [],
                    'days': days,
                    'travel_month': travel_month,
                    'num_people': num_people
                }
                
                # Filter and rank POIs
                ranked_pois = self.matcher.filter_and_rank_pois(pois, user_prefs)
                
                if not ranked_pois:
                    continue
                
                # Select POIs within budget (using per-person budget)
                selected_pois = self.matcher.select_pois_within_budget(
                    ranked_pois,
                    per_person_budget,
                    days
                )
                
                if not selected_pois:
                    continue
                
                # Calculate location score (using per-person budget)
                location_score = self._calculate_location_score(
                    location,
                    selected_pois,
                    per_person_budget,
                    days,
                    travel_month
                )
                
                # Get preview data (using total budget for display, but calculations use per-person)
                preview = self._create_preview(
                    location,
                    selected_pois,
                    budget,
                    days,
                    num_people
                )
                
                scored_locations.append({
                    'location': location,
                    'score': location_score,
                    'preview': preview,
                    'poi_count': len(selected_pois)
                })
            
            if not scored_locations:
                return {
                    'success': False,
                    'error': 'No destinations match your preferences',
                    'suggestion': 'Try increasing budget or broader mood preferences'
                }
            
            # Sort by score (descending)
            scored_locations.sort(key=lambda x: x['score'], reverse=True)
            
            # Get top N recommendations
            recommendations = scored_locations[:num_recommendations]
            
            # Format recommendations
            formatted_recommendations = []
            for idx, rec in enumerate(recommendations, 1):
                formatted_recommendations.append({
                    'rank': idx,
                    'destination': rec['location']['city'],
                    'region': rec['location']['parent_region'],
                    'location_id': rec['location']['location_id'],
                    'match_score': round(rec['score'], 2),
                    'preview': rec['preview']
                })
            
            return {
                'success': True,
                'count': len(formatted_recommendations),
                'recommendations': formatted_recommendations,
                'search_criteria': {
                    'budget': budget,
                    'mood': mood,
                    'activities': activities or [],
                    'days': days,
                    'travel_month': travel_month
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to generate recommendations: {str(e)}'
            }
    
    def _calculate_location_score(
        self,
        location: Dict,
        pois: List[Dict],
        budget: float,
        days: int,
        travel_month: int
    ) -> float:
        """
        Calculate overall score for a location
        
        Args:
            location: Location dictionary
            pois: Selected POIs for location
            budget: Budget
            days: Number of days
            travel_month: Travel month
        
        Returns:
            Score (0-100)
        """
        score = 0.0
        
        # 1. POI Quality (40 points) - based on average POI match score
        if pois:
            avg_poi_score = sum(poi.get('match_score', 0) for poi in pois) / len(pois)
            score += (avg_poi_score / 100) * 40
        
        # 2. POI Quantity (20 points) - more options is better
        poi_count = len(pois)
        if poi_count >= days * 3:  # 3+ POIs per day
            score += 20
        elif poi_count >= days * 2:  # 2 POIs per day
            score += 15
        elif poi_count >= days:  # 1 POI per day
            score += 10
        
        # 3. Budget Fit (20 points)
        total_poi_cost = sum(poi.get('estimated_cost_pkr_max', 0) for poi in pois)
        poi_budget = budget * 0.30  # 30% for attractions
        
        if total_poi_cost <= poi_budget:
            score += 20
        elif total_poi_cost <= poi_budget * 1.2:
            score += 15
        elif total_poi_cost <= poi_budget * 1.5:
            score += 10
        
        # 4. Season Match (10 points) - check if good time to visit
        tourist_season = location.get('tourist_season', '')
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        if travel_month <= 12:
            month_name = month_names[travel_month]
            if month_name in tourist_season:
                score += 10
            else:
                score += 5
        
        # 5. Variety (10 points) - diverse activities
        unique_categories = set(poi.get('category') for poi in pois)
        if len(unique_categories) >= 3:
            score += 10
        elif len(unique_categories) >= 2:
            score += 7
        else:
            score += 3
        
        return min(score, 100)  # Cap at 100
    
    def _create_preview(
        self,
        location: Dict,
        pois: List[Dict],
        budget: float,
        days: int,
        num_people: int = 1
    ) -> Dict:
        """
        Create preview/summary for a destination
        
        Args:
            location: Location dictionary
            pois: Selected POIs
            budget: Budget
            days: Days
        
        Returns:
            Preview dictionary
        """
        # Calculate costs (scale POI costs by num_people, as entry fees are per person)
        per_person_poi_cost = sum(poi.get('estimated_cost_pkr_max', 0) for poi in pois)
        total_poi_cost = per_person_poi_cost * num_people
        
        # Accommodation: may not scale linearly, but for simplicity scale it
        # Food: scales linearly with num_people
        # Transport: may not scale linearly, but for simplicity scale it
        per_person_budget = budget / num_people
        accommodation_cost = (per_person_budget * 0.40) * num_people
        food_cost = (per_person_budget * 0.20) * num_people
        transport_cost = (per_person_budget * 0.10) * num_people
        
        total_estimated = total_poi_cost + accommodation_cost + food_cost + transport_cost
        
        # Get top 3 POIs for preview
        top_pois = pois[:3]
        
        # Collect all photos from top POIs
        preview_photos = []
        for poi in top_pois:
            photos = poi.get('photos', [])
            if photos:
                # Take first photo from each POI
                if isinstance(photos, list) and len(photos) > 0:
                    preview_photos.append({
                        'poi_name': poi['name'],
                        'photo': photos[0],
                        'rating': float(poi.get('rating', 0)) if poi.get('rating') else None
                    })
        
        # If no photos from POIs, create placeholder
        if not preview_photos:
            preview_photos = [{
                'poi_name': location['city'],
                'photo': {
                    'url': f'https://source.unsplash.com/800x600/?{location["city"]},pakistan,travel',
                    'photographer': 'Unsplash'
                },
                'rating': None
            }]
        
        # Get unique activities
        all_activities = []
        for poi in pois:
            activities = poi.get('activities', [])
            if isinstance(activities, list):
                all_activities.extend(activities)
        unique_activities = list(set(all_activities))[:5]  # Top 5 activities
        
        # Get unique categories
        categories = list(set(poi.get('category') for poi in pois if poi.get('category')))
        
        return {
            'title': f"{days}-Day {location['city']} Adventure",
            'destination': location['city'],
            'region': location['parent_region'],
            'days': days,
            'photos': preview_photos[:4],  # Max 4 photos for preview
            'highlights': [poi['name'] for poi in top_pois],
            'activities': unique_activities,
            'categories': categories,
            'cost_estimate': {
                'total_budget': budget,
                'estimated_cost': round(total_estimated, 2),
                'within_budget': total_estimated <= budget,
                'breakdown': {
                    'attractions': round(total_poi_cost, 2),
                    'accommodation': round(accommodation_cost, 2),
                    'food': round(food_cost, 2),
                    'transport': round(transport_cost, 2)
                }
            },
            'poi_count': len(pois),
            'average_rating': round(
                sum(poi.get('rating', 0) for poi in pois if poi.get('rating')) / len([p for p in pois if p.get('rating')]),
                1
            ) if any(poi.get('rating') for poi in pois) else None,
            'location_info': {
                'latitude': float(location['latitude']),
                'longitude': float(location['longitude']),
                'elevation': float(location['elevation']) if location.get('elevation') else None,
                'climate_zone': location.get('climate_zone'),
                'tourist_season': location.get('tourist_season')
            }
        }
    
    def close(self):
        """Close database connection"""
        self.db.close()

