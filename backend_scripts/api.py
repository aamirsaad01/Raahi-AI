from flask import Flask, request, jsonify
from flask_cors import CORS
from checklist_generator import ChecklistGenerator
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ndma_poller import NDMAPoller
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

# Initialize generator once (reuse connection)
generator = None
ndma_poller = None

def get_generator():
    global generator
    if generator is None:
        generator = ChecklistGenerator()
    return generator

def get_ndma_poller():
    """Get or create NDMA poller instance"""
    global ndma_poller
    if ndma_poller is None:
        try:
            ndma_poller = NDMAPoller()
        except Exception as e:
            logger.warning(f"Could not initialize NDMA poller: {e}")
            return None
    return ndma_poller

def run_ndma_scraper_on_startup():
    """Run NDMA scraper once when API starts"""
    try:
        logger.info("🔄 Running NDMA scraper on API startup...")
        poller = get_ndma_poller()
        if poller:
            # Run in background thread to not block API startup
            def scrape():
                try:
                    result = poller.poll()
                    if result.get('success'):
                        logger.info(f"✅ Startup scrape: {result.get('new_advisories', 0)} new advisories")
                    else:
                        logger.warning(f"⚠️ Startup scrape failed: {result.get('error')}")
                except Exception as e:
                    logger.error(f"Error in startup scrape: {e}")
            
            thread = threading.Thread(target=scrape, daemon=True)
            thread.start()
        else:
            logger.warning("⚠️ NDMA poller not available, skipping startup scrape")
    except Exception as e:
        logger.error(f"Error initializing NDMA scraper on startup: {e}")

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME", "raahi_ai"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
        )
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

@app.route('/api/checklist/generate', methods=['POST'])
def generate_checklist():
    """
    Generate packing checklist based on travel parameters
    
    Expected JSON body:
    {
        "region": "Gilgit-Baltistan",
        "area": "Hunza",
        "month": 6,
        "activities": ["hiking", "photography"]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['region', 'area', 'month', 'activities']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract parameters
        region = data['region']
        area = data['area']
        month = int(data['month'])
        activities = data['activities']
        
        # Validate month
        if month < 1 or month > 12:
            return jsonify({
                'success': False,
                'error': 'Month must be between 1 and 12'
            }), 400
        
        # Generate checklist
        gen = get_generator()
        result = gen.generate_checklist(
            area=area,
            region=region,
            month=month,
            activities=activities
        )
        
        if result.get('success'):
            # Convert the checklist to Flutter-friendly format
            flutter_sections = convert_to_flutter_format(result)
            return jsonify({
                'success': True,
                'sections': flutter_sections,
                'metadata': {
                    'destination': result['destination'],
                    'travel_info': result['travel_info'],
                    'activities': result['activities'],
                    'warnings': result.get('warnings', []),
                    'tips': result.get('tips', []),
                    'total_items': result['total_items']
                }
            }), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error generating checklist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def convert_to_flutter_format(checklist):
    """
    Convert backend checklist format to Flutter app format
    
    Returns list of sections with items in the format Flutter expects
    """
    sections = []
    
    for category, items in checklist['items'].items():
        # Handle nested items (like Activity Gear)
        if isinstance(items, dict):
            for subcategory, subitems in items.items():
                flutter_items = [
                    {
                        'id': f"{subcategory.lower().replace(' ', '_')}_{i}",
                        'name': item,
                        'quantity': 1,
                        'checked': False,
                        'notes': None
                    }
                    for i, item in enumerate(subitems)
                ]
                sections.append({
                    'title': f"{category} - {subcategory}",
                    'items': flutter_items
                })
        else:
            # Flat list of items
            flutter_items = [
                {
                    'id': f"{category.lower().replace(' ', '_')}_{i}",
                    'name': item,
                    'quantity': 1,
                    'checked': False,
                    'notes': None
                }
                for i, item in enumerate(items)
            ]
            sections.append({
                'title': category,
                'items': flutter_items
            })
    
    return sections

@app.route('/api/regions', methods=['GET'])
def get_regions():
    """Get list of available regions"""
    try:
        gen = get_generator()
        cursor = gen.conn.cursor()
        cursor.execute("SELECT DISTINCT parent_region FROM location_mapping ORDER BY parent_region")
        regions = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        return jsonify({
            'success': True,
            'regions': regions
        }), 200
    except Exception as e:
        logger.error(f"Error fetching regions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/areas', methods=['GET'])
def get_areas():
    """Get list of areas for a specific region"""
    try:
        region = request.args.get('region')
        if not region:
            return jsonify({
                'success': False,
                'error': 'Region parameter is required'
            }), 400
        
        gen = get_generator()
        cursor = gen.conn.cursor()
        cursor.execute(
            "SELECT city FROM location_mapping WHERE parent_region = %s ORDER BY city",
            (region,)
        )
        areas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        return jsonify({
            'success': True,
            'areas': areas
        }), 200
    except Exception as e:
        logger.error(f"Error fetching areas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/hazards/refresh', methods=['POST'])
def refresh_hazards():
    """
    Manually trigger NDMA scraper to fetch latest advisories
    
    This endpoint is called when user presses refresh button in Flutter app
    """
    try:
        logger.info("🔄 Manual refresh triggered from Flutter app")
        poller = get_ndma_poller()
        
        if not poller:
            return jsonify({
                'success': False,
                'error': 'NDMA poller not available'
            }), 500
        
        # Run scraper
        result = poller.poll()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Hazards refreshed successfully',
                'advisories_found': result.get('advisories_found', 0),
                'new_advisories': result.get('new_advisories', 0),
                'duration_seconds': result.get('duration_seconds', 0)
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 500
            
    except Exception as e:
        logger.error(f"Error refreshing hazards: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== HAZARD API ENDPOINTS ====================

def map_ndma_alert_to_hazard_type(advisory_type: str, title: str, content: str) -> str:
    """Map NDMA advisory type to HazardType"""
    text = (advisory_type + ' ' + title + ' ' + content).lower()
    
    if 'landslide' in text or 'land slide' in text:
        return 'landslide'
    elif 'flood' in text:
        return 'flood'
    elif 'snow' in text or 'snowfall' in text:
        return 'snowfall'
    elif 'road' in text or 'block' in text or 'closure' in text:
        return 'roadblock'
    elif 'protest' in text or 'strike' in text:
        return 'protest'
    elif 'accident' in text or 'crash' in text:
        return 'accident'
    else:
        return 'roadblock'  # Default

def extract_location_from_ndma_alert(alert: dict) -> tuple:
    """Extract location coordinates from NDMA alert"""
    # Try to find location in affected_regions
    regions = alert.get('affected_regions', [])
    if not regions:
        return None, None
    
    # Try to get coordinates from location_mapping for first region
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get a representative location from the region
        for region in regions:
            cursor.execute("""
                SELECT latitude, longitude, city
                FROM location_mapping
                WHERE parent_region = %s
                LIMIT 1
            """, (region,))
            result = cursor.fetchone()
            if result:
                cursor.close()
                conn.close()
                return result['latitude'], result['longitude'], result['city']
        
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error extracting location: {e}")
    
    return None, None, None

@app.route('/api/hazards', methods=['GET'])
def get_hazards():
    """
    Get all hazards (NDMA alerts + user reports)
    
    Query parameters:
    - source: Filter by source (ndma, user, pmd) - optional
    - severity: Filter by severity (low, medium, high, critical) - optional
    - time_window: Filter by time (24h, 7d, 1m, all) - optional, default: all
    """
    try:
        source_filter = request.args.get('source')  # ndma, user, pmd
        severity_filter = request.args.get('severity')
        time_window = request.args.get('time_window', 'all')  # 24h, 7d, 1m, all
        
        hazards = []
        
        # Get NDMA alerts
        if not source_filter or source_filter == 'ndma':
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query for AI-extracted alerts
            query = "SELECT * FROM ndma_alerts_ai WHERE is_active = TRUE"
            params = []
            
            if severity_filter:
                query += " AND severity = %s"
                params.append(severity_filter)
            
            # Time window filter
            if time_window == '24h':
                query += " AND scraped_at >= NOW() - INTERVAL '24 hours'"
            elif time_window == '7d':
                query += " AND scraped_at >= NOW() - INTERVAL '7 days'"
            elif time_window == '1m':
                query += " AND scraped_at >= NOW() - INTERVAL '1 month'"
            
            query += " ORDER BY scraped_at DESC LIMIT 100"
            
            cursor.execute(query, params)
            ndma_alerts = cursor.fetchall()
            
            for alert in ndma_alerts:
                # Use AI-extracted fields directly
                lat = float(alert.get('latitude', 0.0))
                lon = float(alert.get('longitude', 0.0))
                location = alert.get('location_name', 'Unknown')
                hazard_type = alert.get('icon_type', 'roadblock')
                severity = alert.get('severity', 'medium')
                description = alert.get('description', '')
                heading = alert.get('heading', '')
                
                # Map icon_type to HazardType enum
                icon_to_type = {
                    'snowfall': 'snowfall',
                    'flood': 'flood',
                    'landslide': 'landslide',
                    'roadblock': 'roadblock',
                    'protest': 'protest',
                    'accident': 'accident',
                }
                hazard_type = icon_to_type.get(hazard_type, 'roadblock')
                
                # Map severity
                severity_map = {
                    'low': 'low',
                    'medium': 'medium',
                    'high': 'high',
                    'critical': 'critical',
                }
                severity = severity_map.get(severity, 'medium')
                
                # Format timestamp
                timestamp = alert.get('published_date') or alert.get('scraped_at')
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                elif not isinstance(timestamp, datetime):
                    timestamp = datetime.now()
                
                # Build hazard object
                hazard = {
                    'id': f"ndma_{alert['alert_id']}",
                    'type': hazard_type,
                    'severity': severity,
                    'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
                    'source': alert.get('source', 'NDMA'),
                    'lat': lat,
                    'lon': lon,
                    'location': location,
                    'description': description or heading,  # Use description or heading as fallback
                    'advisory_url': alert.get('advisory_url'),
                    'advisory_type': heading,  # Use heading as advisory type
                }
                
                hazards.append(hazard)
            
            cursor.close()
            conn.close()
        
        # Get user-reported hazards
        if not source_filter or source_filter == 'user':
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM hazard_reports WHERE 1=1"
            params = []
            
            if severity_filter:
                query += " AND severity = %s"
                params.append(severity_filter)
            
            # Time window filter
            if time_window == '24h':
                query += " AND reported_at >= NOW() - INTERVAL '24 hours'"
            elif time_window == '7d':
                query += " AND reported_at >= NOW() - INTERVAL '7 days'"
            elif time_window == '1m':
                query += " AND reported_at >= NOW() - INTERVAL '1 month'"
            
            query += " ORDER BY reported_at DESC LIMIT 100"
            
            cursor.execute(query, params)
            user_reports = cursor.fetchall()
            
            for report in user_reports:
                # Try to extract lat/lon from location string or use defaults
                lat = 0.0
                lon = 0.0
                if report['location']:
                    # Simple parsing - could be improved
                    location_str = report['location']
                    # Try to extract coordinates if present
                    import re
                    coords = re.findall(r'-?\d+\.?\d*', location_str)
                    if len(coords) >= 2:
                        try:
                            lat = float(coords[0])
                            lon = float(coords[1])
                        except:
                            pass
                
                hazards.append({
                    'id': f"user_{report['hazard_id']}",
                    'type': 'roadblock',  # Default, could be stored in DB
                    'severity': report['severity'],
                    'timestamp': report['reported_at'].isoformat() if report['reported_at'] else datetime.now().isoformat(),
                    'source': 'User',
                    'lat': lat,
                    'lon': lon,
                    'location': report['location'] or 'Unknown',
                    'description': report['description'] or report['title'],
                })
            
            cursor.close()
            conn.close()
        
        return jsonify({
            'success': True,
            'hazards': hazards,
            'count': len(hazards)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching hazards: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hazards/report', methods=['POST'])
def report_hazard():
    """
    Submit a new user-reported hazard
    
    Expected JSON body:
    {
        "type": "roadblock",
        "severity": "medium",
        "location": "Karimabad, Hunza",
        "lat": 35.9208,
        "lon": 74.3089,
        "description": "Road blocked due to landslide"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'severity', 'location', 'lat', 'lon']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate severity
        valid_severities = ['low', 'medium', 'high', 'critical']
        if data['severity'] not in valid_severities:
            return jsonify({
                'success': False,
                'error': f'Severity must be one of: {", ".join(valid_severities)}'
            }), 400
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create title from type and location
        title = f"{data['type'].replace('_', ' ').title()} - {data['location']}"
        
        cursor.execute("""
            INSERT INTO hazard_reports (title, description, severity, location, user_id)
            VALUES (%s, %s, %s, %s, NULL)
            RETURNING hazard_id, reported_at
        """, (
            title,
            data.get('description', ''),
            data['severity'],
            f"{data['location']} ({data['lat']}, {data['lon']})"
        ))
        
        result = cursor.fetchone()
        hazard_id = result[0]
        reported_at = result[1]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'hazard_id': hazard_id,
            'reported_at': reported_at.isoformat(),
            'message': 'Hazard reported successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error reporting hazard: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hazards/my-reports', methods=['GET'])
def get_my_reports():
    """
    Get user's reported hazards
    
    Note: Currently returns all user reports since we don't have authentication.
    In production, filter by user_id from session/token.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM hazard_reports
            ORDER BY reported_at DESC
            LIMIT 50
        """)
        
        reports = cursor.fetchall()
        cursor.close()
        conn.close()
        
        hazards = []
        for report in reports:
            # Extract coordinates from location string
            lat = 0.0
            lon = 0.0
            location = report['location'] or 'Unknown'
            
            if report['location']:
                import re
                coords = re.findall(r'-?\d+\.?\d*', report['location'])
                if len(coords) >= 2:
                    try:
                        lat = float(coords[0])
                        lon = float(coords[1])
                    except:
                        pass
            
            hazards.append({
                'id': f"user_{report['hazard_id']}",
                'type': 'roadblock',  # Default
                'severity': report['severity'],
                'timestamp': report['reported_at'].isoformat() if report['reported_at'] else datetime.now().isoformat(),
                'source': 'You',
                'lat': lat,
                'lon': lon,
                'location': location,
                'description': report['description'] or report['title'],
            })
        
        return jsonify({
            'success': True,
            'hazards': hazards,
            'count': len(hazards)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user reports: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Run NDMA scraper on startup (in background thread)
    run_ndma_scraper_on_startup()
    
    logger.info("🚀 Starting Flask API server on http://0.0.0.0:5000")
    logger.info("📡 NDMA scraper will run on startup and when /api/hazards/refresh is called")
    app.run(host='0.0.0.0', port=5000, debug=True)