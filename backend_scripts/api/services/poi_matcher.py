"""
POI Matcher Service
Matches POIs with user preferences and ranks them
"""

from typing import List, Dict, Optional
from datetime import datetime


class POIMatcher:
    """Match POIs to user preferences"""
    
    # Month name mapping
    MONTHS = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    
    # Season mapping
    SEASON_MONTHS = {
        'Spring': [3, 4, 5],
        'Summer': [6, 7, 8],
        'Autumn': [9, 10, 11],
        'Winter': [12, 1, 2],
        'Monsoon': [7, 8, 9]
    }
    
    @staticmethod
    def get_season(month: int) -> str:
        """Get season from month number"""
        for season, months in POIMatcher.SEASON_MONTHS.items():
            if month in months:
                if season != 'Monsoon':  # Prefer primary seasons
                    return season
        return 'Summer'
    
    @staticmethod
    def is_good_time_to_visit(poi: Dict, travel_month: int) -> bool:
        """
        Check if travel month is good for visiting POI
        
        Args:
            poi: POI dictionary
            travel_month: Month number (1-12)
        
        Returns:
            True if good time to visit
        """
        best_months = poi.get('best_months', '')
        if not best_months:
            return True  # No restriction
        
        month_name = POIMatcher.MONTHS.get(travel_month, '')
        
        # Check if month name is in best_months string
        if month_name in best_months:
            return True
        
        # Check month number
        if str(travel_month) in best_months:
            return True
        
        # Check month ranges like "March-October"
        try:
            if '-' in best_months:
                parts = best_months.split('-')
                if len(parts) == 2:
                    start_month = list(POIMatcher.MONTHS.keys())[
                        list(POIMatcher.MONTHS.values()).index(parts[0].strip())
                    ]
                    end_month = list(POIMatcher.MONTHS.keys())[
                        list(POIMatcher.MONTHS.values()).index(parts[1].strip())
                    ]
                    
                    # Handle year wrap-around (e.g., November-February)
                    if start_month <= end_month:
                        return start_month <= travel_month <= end_month
                    else:
                        return travel_month >= start_month or travel_month <= end_month
        except (ValueError, IndexError):
            pass
        
        return True  # Default to allowing if parsing fails
    
    @staticmethod
    def calculate_match_score(
        poi: Dict,
        user_prefs: Dict
    ) -> float:
        """
        Calculate how well a POI matches user preferences
        
        Args:
            poi: POI dictionary
            user_prefs: User preferences
        
        Returns:
            Match score (0-100)
        """
        score = 0.0
        
        # 1. Rating (30 points max)
        rating = poi.get('rating', 0)
        if rating:
            score += (rating / 5.0) * 30
        
        # 2. Mood match (25 points max)
        user_moods = set(user_prefs.get('mood', []))
        poi_moods = set(poi.get('mood_tags', []))
        if user_moods and poi_moods:
            mood_overlap = len(user_moods & poi_moods)
            score += (mood_overlap / len(user_moods)) * 25
        
        # 3. Activity match (25 points max)
        user_activities = set(user_prefs.get('activities', []))
        poi_activities = set(poi.get('activities', []))
        if user_activities and poi_activities:
            activity_overlap = len(user_activities & poi_activities)
            score += (activity_overlap / len(user_activities)) * 25
        
        # 4. Budget match (10 points max)
        poi_cost = poi.get('estimated_cost_pkr_max', 0)
        daily_budget = user_prefs.get('budget', 0) / user_prefs.get('days', 1)
        poi_budget_limit = daily_budget * 0.4  # 40% of daily budget for activities
        
        if poi_cost <= poi_budget_limit:
            score += 10
        elif poi_cost <= poi_budget_limit * 1.5:
            score += 5
        
        # 5. Season match (10 points max)
        if POIMatcher.is_good_time_to_visit(poi, user_prefs.get('travel_month', 5)):
            score += 10
        
        return score
    
    @staticmethod
    def filter_and_rank_pois(
        pois: List[Dict],
        user_prefs: Dict
    ) -> List[Dict]:
        """
        Filter and rank POIs based on user preferences
        
        Args:
            pois: List of POIs
            user_prefs: User preferences
        
        Returns:
            Sorted list of POIs with match scores
        """
        scored_pois = []
        
        for poi in pois:
            # Calculate match score
            score = POIMatcher.calculate_match_score(poi, user_prefs)
            
            # Only include POIs with reasonable match (>30% match)
            if score >= 30:
                poi_copy = poi.copy()
                poi_copy['match_score'] = round(score, 2)
                scored_pois.append(poi_copy)
        
        # Sort by match score (descending)
        scored_pois.sort(key=lambda x: x['match_score'], reverse=True)
        
        return scored_pois
    
    @staticmethod
    def select_pois_within_budget(
        pois: List[Dict],
        total_budget: float,
        num_days: int,
        budget_allocation: Dict = None
    ) -> List[Dict]:
        """
        Select POIs that fit within budget
        Solution 1: Ensures minimum 1 POI per day
        
        Args:
            pois: Ranked list of POIs
            total_budget: Total trip budget
            num_days: Number of days
            budget_allocation: Budget breakdown (optional)
        
        Returns:
            List of selected POIs
        """
        if budget_allocation is None:
            budget_allocation = {
                'pois': 0.30,      # 30% for attractions
                'hotels': 0.40,    # 40% for accommodation
                'food': 0.20,      # 20% for food
                'transport': 0.10  # 10% for transport
            }
        
        # Convert to float to avoid Decimal issues
        total_budget = float(total_budget)
        poi_budget = total_budget * budget_allocation['pois']
        selected = []
        cost_so_far = 0
        
        # Solution 1: Minimum POIs per day - ensure at least num_days POIs
        min_pois_needed = num_days  # At least 1 POI per day
        
        for poi in pois:
            poi_cost = float(poi.get('estimated_cost_pkr_max', 0))
            
            # If we haven't reached minimum, prioritize getting at least 1 per day
            # even if it slightly exceeds budget
            if len(selected) < min_pois_needed:
                # For minimum POIs, allow slight budget flexibility (up to 120% of budget)
                if cost_so_far + poi_cost <= poi_budget * 1.2:
                    selected.append(poi)
                    cost_so_far += poi_cost
                    continue
            
            # After minimum is met, stick to budget strictly
            if cost_so_far + poi_cost <= poi_budget:
                selected.append(poi)
                cost_so_far += poi_cost
                
                # Aim for 2-4 POIs per day on average
                if len(selected) >= num_days * 3:
                    break
        
        return selected
    
    @staticmethod
    def estimate_time_for_poi(poi: Dict) -> float:
        """
        Estimate time needed for POI including travel
        
        Args:
            poi: POI dictionary
        
        Returns:
            Hours needed (including buffer)
        """
        base_duration = float(poi.get('avg_duration_hours', 2.0))
        
        # Add buffer time for travel, breaks, etc.
        buffer = 1.0  # 1 hour buffer
        
        return base_duration + buffer

