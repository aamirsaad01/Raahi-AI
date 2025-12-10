"""
Raahi AI - Backend API Server
Flask application for itinerary generation and management
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.auth import auth_bp
from api.routes.itinerary import itinerary_bp

# Create Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Enable CORS for mobile app
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(itinerary_bp)


@app.route('/')
def home():
    """Root endpoint"""
    return jsonify({
        'name': 'Raahi AI Backend API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login'
            },
            'itinerary': {
                'recommend': 'POST /api/itinerary/recommend (NEW!)',
                'generate': 'POST /api/itinerary/generate',
                'get': 'GET /api/itinerary/<id>',
                'user_itineraries': 'GET /api/itinerary/user/<user_id>',
                'update': 'PUT /api/itinerary/<id>',
                'delete': 'DELETE /api/itinerary/<id>'
            }
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running'
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    
    print("\n" + "="*60)
    print("🚀 Raahi AI Backend API Server")
    print("="*60)
    print(f"📍 Running on: http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )

