"""
Itinerary API Routes
Endpoints for itinerary generation and management
"""

from flask import Blueprint, request, jsonify
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.services.itinerary_generator import ItineraryGenerator
from api.services.itinerary_recommender import ItineraryRecommender

# Create blueprint
itinerary_bp = Blueprint('itinerary', __name__, url_prefix='/api/itinerary')


@itinerary_bp.route('/recommend', methods=['POST'])
def recommend_destinations():
    """
    Recommend destination options based on budget and mood
    
    POST /api/itinerary/recommend
    
    Request Body:
    {
        "budget": 50000,
        "mood": ["adventurous", "romantic"],
        "activities": ["hiking", "photography"],  (optional)
        "days": 3,  (optional, default: 3)
        "travel_month": 5,  (optional, default: 5)
        "num_recommendations": 5  (optional, default: 5)
    }
    
    Response:
    {
        "success": true,
        "count": 5,
        "recommendations": [
            {
                "rank": 1,
                "destination": "Hunza",
                "region": "Gilgit-Baltistan",
                "location_id": 45,
                "match_score": 87.5,
                "preview": {
                    "title": "3-Day Hunza Adventure",
                    "photos": [
                        {
                            "poi_name": "Attabad Lake",
                            "photo": {"url": "...", "photographer": "..."},
                            "rating": 4.5
                        }
                    ],
                    "highlights": ["Attabad Lake", "Rakaposhi Base Camp", "Eagle's Nest"],
                    "activities": ["hiking", "photography", "boating"],
                    "cost_estimate": {...},
                    "poi_count": 6,
                    "average_rating": 4.3
                }
            }
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'budget' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: budget'
            }), 400
        
        if 'mood' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: mood'
            }), 400
        
        # Validate data types
        if not isinstance(data['budget'], (int, float)) or data['budget'] <= 0:
            return jsonify({
                'success': False,
                'error': 'Budget must be a positive number'
            }), 400
        
        if not isinstance(data['mood'], list) or len(data['mood']) == 0:
            return jsonify({
                'success': False,
                'error': 'Mood must be a non-empty list'
            }), 400
        
        # Set defaults
        days = data.get('days', 3)
        travel_month = data.get('travel_month', 5)
        num_recommendations = data.get('num_recommendations', 5)
        activities = data.get('activities', [])
        num_people = data.get('num_people', 1)  # Default to 1 person
        
        # Validate num_people
        if not isinstance(num_people, int) or num_people < 1:
            return jsonify({
                'success': False,
                'error': 'Number of people must be a positive integer'
            }), 400
        
        # Generate recommendations
        recommender = ItineraryRecommender()
        result = recommender.recommend_destinations(
            budget=data['budget'],
            mood=data['mood'],
            activities=activities,
            days=days,
            travel_month=travel_month,
            num_recommendations=num_recommendations,
            num_people=num_people
        )
        recommender.close()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@itinerary_bp.route('/generate', methods=['POST'])
def generate_itinerary():
    """
    Generate new itinerary
    
    POST /api/itinerary/generate
    
    Request Body:
    {
        "user_id": 1,  (optional, defaults to 0 for anonymous users)
        "destination": "Hunza",
        "days": 3,
        "budget": 50000,
        "mood": ["adventurous", "romantic"],
        "activities": ["hiking", "photography"],
        "travel_month": 5,
        "start_date": "2025-05-10" (optional)
    }
    
    Response:
    {
        "success": true,
        "itinerary_id": 123,
        "title": "3-Day Adventure Hunza Trip",
        "daily_plan": [...],
        ...
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields (user_id is optional)
        required_fields = ['destination', 'days', 'budget']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # user_id is optional - if not provided or 0, will be set to None (anonymous user)
        if 'user_id' not in data or data.get('user_id') is None or data.get('user_id') == 0:
            data['user_id'] = None
        
        # Validate data types
        if not isinstance(data['days'], int) or data['days'] <= 0:
            return jsonify({
                'success': False,
                'error': 'Days must be a positive integer'
            }), 400
        
        if not isinstance(data['budget'], (int, float)) or data['budget'] <= 0:
            return jsonify({
                'success': False,
                'error': 'Budget must be a positive number'
            }), 400
        
        # Set defaults
        if 'mood' not in data:
            data['mood'] = []
        if 'activities' not in data:
            data['activities'] = []
        if 'travel_month' not in data:
            data['travel_month'] = 5  # Default to May
        if 'num_people' not in data:
            data['num_people'] = 1  # Default to 1 person
        
        # Validate num_people
        if not isinstance(data['num_people'], int) or data['num_people'] < 1:
            return jsonify({
                'success': False,
                'error': 'Number of people must be a positive integer'
            }), 400
        
        # Generate itinerary
        generator = ItineraryGenerator()
        result = generator.generate(data)
        generator.close()
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@itinerary_bp.route('/<int:itinerary_id>', methods=['GET'])
def get_itinerary(itinerary_id):
    """
    Get itinerary by ID
    
    GET /api/itinerary/123
    
    Response:
    {
        "success": true,
        "itinerary": {...}
    }
    """
    try:
        generator = ItineraryGenerator()
        result = generator.get_itinerary(itinerary_id)
        generator.close()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@itinerary_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_itineraries(user_id):
    """
    Get all itineraries for a user
    
    GET /api/itinerary/user/1
    
    Response:
    {
        "success": true,
        "count": 5,
        "itineraries": [...]
    }
    """
    try:
        generator = ItineraryGenerator()
        result = generator.get_user_itineraries(user_id)
        generator.close()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@itinerary_bp.route('/<int:itinerary_id>', methods=['PUT'])
def update_itinerary(itinerary_id):
    """
    Update itinerary
    
    PUT /api/itinerary/123
    
    Request Body:
    {
        "title": "New Title",
        "days": 4,
        "budget": 60000
    }
    
    Response:
    {
        "success": true,
        "message": "Itinerary updated successfully"
    }
    """
    try:
        data = request.get_json()
        
        generator = ItineraryGenerator()
        result = generator.update_itinerary(itinerary_id, data)
        generator.close()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@itinerary_bp.route('/<int:itinerary_id>', methods=['DELETE'])
def delete_itinerary(itinerary_id):
    """
    Delete itinerary
    
    DELETE /api/itinerary/123
    
    Response:
    {
        "success": true,
        "message": "Itinerary deleted successfully"
    }
    """
    try:
        generator = ItineraryGenerator()
        result = generator.delete_itinerary(itinerary_id)
        generator.close()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

