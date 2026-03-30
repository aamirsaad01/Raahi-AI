"""
Raahi AI - Backend API Server
Unified Flask application for itinerary generation, hazard alerts, and packing checklists
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
import threading

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.auth import auth_bp
from api.routes.itinerary import itinerary_bp
from checklist_generator import ChecklistGenerator
from ndma_poller import NDMAPoller
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(repo_root, '.env')
load_dotenv(dotenv_path=env_path)

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

# Register blueprints (Itinerary & Auth)
app.register_blueprint(auth_bp)
app.register_blueprint(itinerary_bp)

# ==================== GLOBAL INITIALIZATION ====================

# Initialize shared services
generator = None
ndma_poller = None

def get_generator():
    """Get or create ChecklistGenerator instance"""
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

# ==================== PACKING CHECKLIST ENDPOINTS ====================

def convert_to_flutter_format(checklist):
    """Convert backend checklist format to Flutter app format"""
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

@app.route('/api/checklist/generate', methods=['POST'])
def generate_checklist():
    """Generate packing checklist based on travel parameters"""
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

# ==================== HAZARD ALERT ENDPOINTS ====================

@app.route('/api/hazards/refresh', methods=['POST'])
def refresh_hazards():
    """Manually trigger NDMA scraper to fetch latest advisories"""
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

@app.route('/api/hazards', methods=['GET'])
def get_hazards():
    """Get all hazards (NDMA alerts + user reports)"""
    try:
        source_filter = request.args.get('source')  # ndma, user, pmd
        severity_filter = request.args.get('severity')
        time_window = request.args.get('time_window', 'all')  # 24h, 7d, 1m, all
        
        hazards = []
        
        # Get NDMA alerts from the new AI-extracted table
        if not source_filter or source_filter == 'ndma':
            try:
                conn = get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # First check if table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'ndma_alerts_ai'
                    ) as exists;
                """)
                result = cursor.fetchone()
                table_exists = result['exists'] if result else False
                
                if not table_exists:
                    logger.warning("Table 'ndma_alerts_ai' does not exist. Please run create_ndma_ai_table.py")
                    cursor.close()
                    conn.close()
                else:
                    # Build query for ndma_alerts_ai
                    # Try with is_active first, but also check if column exists
                    query = "SELECT * FROM ndma_alerts_ai"
                    params = []
                    
                    # Check if is_active column exists
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='ndma_alerts_ai' AND column_name='is_active'
                    """)
                    has_is_active = cursor.fetchone() is not None
                    
                    if has_is_active:
                        query += " WHERE (is_active = TRUE OR is_active IS NULL)"  # Include NULL as active
                    else:
                        query += " WHERE 1=1"  # No filter if column doesn't exist
                    
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
                    
                    logger.info(f"Found {len(ndma_alerts)} NDMA alerts from database")
            
                    for alert in ndma_alerts:
                        # Use AI-extracted fields directly
                        lat = float(alert.get('latitude', 0.0)) if alert.get('latitude') else 0.0
                        lon = float(alert.get('longitude', 0.0)) if alert.get('longitude') else 0.0
                        location = alert.get('location_name', 'Unknown') or 'Unknown'
                        hazard_type = alert.get('icon_type', 'roadblock') or 'roadblock'
                        severity = alert.get('severity', 'medium') or 'medium'
                        description = alert.get('description', '') or ''
                        heading = alert.get('heading', '') or ''
                        
                        # Map icon_type to HazardType enum
                        icon_to_type = {
                            'snowfall': 'snowfall',
                            'flood': 'flood',
                            'landslide': 'landslide',
                            'roadblock': 'roadblock',
                            'protest': 'protest',
                            'accident': 'accident',
                            'drought': 'drought',
                            'heatwave': 'heatwave',
                            'earthquake': 'earthquake',
                            'tsunami': 'tsunami',
                            'cyclone': 'cyclone',
                            'fire': 'fire',
                            'general_hazard': 'roadblock',
                        }
                        hazard_type = icon_to_type.get(hazard_type.lower() if hazard_type else 'roadblock', 'roadblock')
                        
                        # Map severity
                        severity_map = {
                            'low': 'low',
                            'medium': 'medium',
                            'high': 'high',
                            'critical': 'critical',
                        }
                        severity = severity_map.get(severity.lower() if severity else 'medium', 'medium')
                        
                        # Format timestamp - prioritize published_date (actual alert date), then scraped_at, then created_at
                        # published_date is DATE (when alert was published by NDMA)
                        # scraped_at is TIMESTAMPTZ (when we scraped it)
                        from datetime import date as date_type
                        
                        published_date = alert.get('published_date')
                        scraped_at = alert.get('scraped_at')
                        created_at = alert.get('created_at')
                        
                        # Prioritize published_date, then scraped_at, then created_at
                        # Check explicitly for None (not just falsy) since date(2000,1,1) would be falsy in some contexts
                        if published_date is not None:
                            timestamp = published_date
                            logger.info(f"Alert {alert.get('alert_id')}: Using published_date: {published_date} (type: {type(published_date).__name__})")
                        elif scraped_at is not None:
                            timestamp = scraped_at
                            logger.info(f"Alert {alert.get('alert_id')}: published_date is NULL, using scraped_at: {scraped_at} (type: {type(scraped_at).__name__})")
                        elif created_at is not None:
                            timestamp = created_at
                            logger.info(f"Alert {alert.get('alert_id')}: Using created_at: {created_at}")
                        else:
                            # If all are None, this is a data issue - use scraped_at which should always exist
                            # But log a warning
                            timestamp = datetime.now(timezone.utc)
                            logger.warning(f"Alert {alert.get('alert_id')}: All timestamps are None! Using current time as fallback")
                        
                        # Convert to timezone-aware datetime
                        if isinstance(timestamp, str):
                            try:
                                if timestamp.endswith('Z'):
                                    timestamp = timestamp.replace('Z', '+00:00')
                                timestamp = datetime.fromisoformat(timestamp)
                                # Ensure timezone-aware
                                if timestamp.tzinfo is None:
                                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                            except Exception as e:
                                logger.warning(f"Error parsing timestamp string '{timestamp}': {e}")
                                timestamp = datetime.now(timezone.utc)
                        elif isinstance(timestamp, date_type) and not isinstance(timestamp, datetime):
                            # datetime.date object (from PostgreSQL DATE column) - convert to datetime (midnight) with timezone
                            timestamp = datetime.combine(timestamp, datetime.min.time()).replace(tzinfo=timezone.utc)
                        elif isinstance(timestamp, datetime):
                            # Ensure timezone-aware
                            if timestamp.tzinfo is None:
                                timestamp = timestamp.replace(tzinfo=timezone.utc)
                        else:
                            # Fallback to current time
                            logger.warning(f"Alert {alert.get('alert_id')}: Unknown timestamp type: {type(timestamp)}, value: {timestamp}")
                            timestamp = datetime.now(timezone.utc)
                        
                        # Build hazard object
                        hazard = {
                            'id': f"ndma_{alert.get('alert_id', 0)}",
                            'type': hazard_type,
                            'severity': severity,
                            'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
                            'source': alert.get('source', 'NDMA') or 'NDMA',
                            'lat': lat,
                            'lon': lon,
                            'location': location,
                            'description': description or heading,
                            'advisory_url': alert.get('advisory_url'),
                            'advisory_type': heading,
                        }
                        
                        hazards.append(hazard)
                    
                    cursor.close()
                    conn.close()
            except Exception as db_error:
                logger.error(f"Database error fetching NDMA alerts: {db_error}", exc_info=True)
                # Continue to try user reports even if NDMA fails
        
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
                # Get coordinates - check if latitude/longitude columns exist
                lat = 0.0
                lon = 0.0
                location_name = report.get('location', 'Unknown')
                
                # Try to get from latitude/longitude columns first
                if 'latitude' in report and 'longitude' in report:
                    lat = float(report['latitude']) if report['latitude'] else 0.0
                    lon = float(report['longitude']) if report['longitude'] else 0.0
                else:
                    # Fallback: Extract coordinates from location string
                    if report['location']:
                        import re
                        coords = re.findall(r'-?\d+\.?\d*', report['location'])
                        if len(coords) >= 2:
                            try:
                                lat = float(coords[0])
                                lon = float(coords[1])
                                # Extract location name (remove coordinates)
                                location_name = re.sub(r'\s*\([^)]*\)\s*', '', report['location']).strip()
                            except:
                                pass
                
                # Get hazard type
                hazard_type = report.get('hazard_type', 'roadblock')
                if not hazard_type:
                    # Try to infer from title
                    title = report.get('title', '')
                    if 'snow' in title.lower():
                        hazard_type = 'snowfall'
                    elif 'flood' in title.lower():
                        hazard_type = 'flood'
                    elif 'landslide' in title.lower():
                        hazard_type = 'landslide'
                    else:
                        hazard_type = 'roadblock'
                
                # Handle reported_at timestamp - ensure it's timezone-aware
                reported_at = report['reported_at']
                if reported_at:
                    # If it's a datetime object, ensure it's timezone-aware
                    if isinstance(reported_at, datetime):
                        if reported_at.tzinfo is None:
                            # Make it timezone-aware (assume UTC)
                            reported_at = reported_at.replace(tzinfo=timezone.utc)
                        timestamp_str = reported_at.isoformat()
                    else:
                        timestamp_str = str(reported_at)
                else:
                    timestamp_str = datetime.now(timezone.utc).isoformat()
                
                hazards.append({
                    'id': f"user_{report['hazard_id']}",
                    'type': hazard_type,
                    'severity': report['severity'],
                    'timestamp': timestamp_str,
                    'source': 'Crowd-Sourced',
                    'lat': lat,
                    'lon': lon,
                    'location': location_name,
                    'description': report.get('description', '') or report.get('title', ''),
                    'advisory_type': report.get('title', ''),  # Use title as advisory_type
                })
            
            cursor.close()
            conn.close()

        # Sort all hazards by timestamp (most recent first)
        # reverse=True means newest timestamps (largest values) come first
        if hazards:
            def safe_sort_key(x):
                try:
                    ts = x.get('timestamp')
                    if ts is None:
                        return datetime.min.replace(tzinfo=timezone.utc)  # Put null timestamps at end
                    
                    if isinstance(ts, str):
                        # Parse ISO format string
                        if ts.endswith('Z'):
                            ts = ts.replace('Z', '+00:00')
                        parsed = datetime.fromisoformat(ts)
                        # Ensure timezone-aware (default to UTC if naive)
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=timezone.utc)
                        return parsed
                    elif isinstance(ts, datetime):
                        # Ensure timezone-aware
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        return ts
                    else:
                        return datetime.min.replace(tzinfo=timezone.utc)  # Put invalid timestamps at end
                except Exception as e:
                    logger.warning(f"Error parsing timestamp for sorting: {e}, putting at end")
                    return datetime.min.replace(tzinfo=timezone.utc)  # Put errors at end
            
            # Sort with reverse=True: newest (largest timestamp) first
            hazards.sort(key=safe_sort_key, reverse=True)
        
        # Add diagnostic info if no hazards found
        response_data = {
            'success': True, 
            'hazards': hazards,
            'count': len(hazards)
        }
        
        if len(hazards) == 0:
            # Check if table exists and has any data
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Check table existence
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'ndma_alerts_ai'
                    ) as exists;
                """)
                result = cursor.fetchone()
                table_exists = result['exists'] if result else False
                
                if table_exists:
                    # Count total records
                    cursor.execute("SELECT COUNT(*) FROM ndma_alerts_ai")
                    total_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM ndma_alerts_ai WHERE is_active = TRUE")
                    active_count = cursor.fetchone()[0]
                    
                    response_data['diagnostics'] = {
                        'table_exists': True,
                        'total_records': total_count,
                        'active_records': active_count,
                        'message': f'Table exists with {total_count} total records ({active_count} active). Try refreshing or adjusting filters.'
                    }
                else:
                    response_data['diagnostics'] = {
                        'table_exists': False,
                        'message': 'Table ndma_alerts_ai does not exist. Please run create_ndma_ai_table.py first.'
                    }
                
                cursor.close()
                conn.close()
            except Exception as diag_error:
                logger.warning(f"Could not get diagnostics: {diag_error}")
                response_data['diagnostics'] = {
                    'message': 'Unable to check database status. Please ensure the database is accessible.'
                }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error fetching hazards: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/hazards/report', methods=['POST'])
def report_hazard():
    """Submit a new user-reported hazard"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'severity', 'location', 'title']
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
        
        # Geocode location name to get coordinates
        location_name = data['location'].strip()
        lat, lon = _geocode_location(location_name)
        
        if lat is None or lon is None:
            return jsonify({
                'success': False,
                'error': f'Could not find coordinates for location: {location_name}. Please provide a more specific location name.'
            }), 400
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hazard_type column exists, otherwise use type
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='hazard_reports' AND column_name='hazard_type'
        """)
        has_hazard_type = cursor.fetchone() is not None
        
        if has_hazard_type:
            cursor.execute("""
                INSERT INTO hazard_reports (title, description, severity, location, hazard_type, latitude, longitude, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)
                RETURNING hazard_id, reported_at
            """, (
                data['title'],
                data.get('description', ''),
                data['severity'],
                location_name,
                data['type'],
                lat,
                lon
            ))
        else:
            # Fallback: store coordinates in location field if columns don't exist
            cursor.execute("""
                INSERT INTO hazard_reports (title, description, severity, location, user_id)
                VALUES (%s, %s, %s, %s, NULL)
                RETURNING hazard_id, reported_at
            """, (
                data['title'],
                data.get('description', ''),
                data['severity'],
                f"{location_name} ({lat}, {lon})"
            ))
        
        result = cursor.fetchone()
        hazard_id = result[0]
        reported_at = result[1]
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ Hazard reported: {data['title']} at {location_name} ({lat}, {lon})")
        
        return jsonify({
            'success': True,
            'hazard_id': hazard_id,
            'reported_at': reported_at.isoformat(),
            'message': 'Hazard reported successfully',
            'location': location_name,
            'lat': lat,
            'lon': lon
        }), 201
        
    except Exception as e:
        logger.error(f"Error reporting hazard: {e}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _geocode_location(location_name: str) -> tuple:
    """
    Geocode location name to get coordinates using Nominatim (OSM)
    
    Args:
        location_name: Name of the location (e.g., "Murree", "Naran", "Gilgit")
        
    Returns:
        Tuple of (latitude, longitude) or (None, None) if not found
    """
    try:
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut, GeocoderServiceError
        
        # Initialize geocoder
        geolocator = Nominatim(user_agent="raahi_ai_hazard_reports", timeout=10)
        
        # Try with "Pakistan" suffix for better results
        search_queries = [
            f"{location_name}, Pakistan",
            location_name,
            f"{location_name}, PK"
        ]
        
        for query in search_queries:
            try:
                location = geolocator.geocode(query)
                if location:
                    logger.info(f"✅ Geocoded '{location_name}' → ({location.latitude}, {location.longitude})")
                    return (float(location.latitude), float(location.longitude))
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                logger.warning(f"Geocoding error for '{query}': {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected geocoding error for '{query}': {e}")
                continue
        
        logger.warning(f"⚠️ Could not geocode location: {location_name}")
        return (None, None)
        
    except ImportError:
        logger.error("geopy not installed. Install with: pip install geopy")
        return (None, None)
    except Exception as e:
        logger.error(f"Error in geocoding: {e}")
        return (None, None)

@app.route('/api/hazards/my-reports', methods=['GET'])
def get_my_reports():
    """Get user's reported hazards"""
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
                'type': 'roadblock',  # Default, could be stored in DB
                'severity': report['severity'],
                'timestamp': report['reported_at'].isoformat() if report['reported_at'] else datetime.now().isoformat(),
                'source': 'Crowd-Sourced',
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


@app.route('/')
def home():
    """Root endpoint - shows all available endpoints"""
    return jsonify({
        'name': 'Raahi AI Backend API',
        'version': '2.0.0',
        'status': 'running',
        'description': 'Unified API for itinerary generation, hazard alerts, and packing checklists',
        'endpoints': {
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login'
            },
            'itinerary': {
                'recommend': 'POST /api/itinerary/recommend',
                'generate': 'POST /api/itinerary/generate',
                'get': 'GET /api/itinerary/<id>',
                'user_itineraries': 'GET /api/itinerary/user/<user_id>',
                'update': 'PUT /api/itinerary/<id>',
                'delete': 'DELETE /api/itinerary/<id>'
            },
            'hazards': {
                'get': 'GET /api/hazards',
                'report': 'POST /api/hazards/report',
                'my_reports': 'GET /api/hazards/my-reports',
                'refresh': 'POST /api/hazards/refresh'
            },
            'packing': {
                'generate': 'POST /api/checklist/generate',
                'regions': 'GET /api/regions',
                'areas': 'GET /api/areas?region=<region>'
            },
            'health': {
                'check': 'GET /api/health'
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

@app.route('/health', methods=['GET'])
def health_check_legacy():
    """Legacy health check endpoint (backward compatibility)"""
    return jsonify({'status': 'healthy'}), 200


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
    # Run NDMA scraper on startup (in background thread)
    # NDMA scraper disabled - run manually with: python ndma_poller.py --once
    # run_ndma_scraper_on_startup()
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    
    print("\n" + "="*60)
    print("🚀 Raahi AI Backend API Server (Unified)")
    print("="*60)
    print(f"📍 Running on: http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}")
    print("\n📡 Features:")
    print("   ✅ Itinerary Generation")
    print("   ✅ Hazard Alerts (NDMA)")
    print("   ✅ Packing Checklists")
    print("   ✅ User Authentication")
    print("="*60 + "\n")
    
    logger.info("🚀 Starting Flask API server on http://0.0.0.0:5000")
    logger.info("📡 NDMA scraper will run on startup and when /api/hazards/refresh is called")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )

