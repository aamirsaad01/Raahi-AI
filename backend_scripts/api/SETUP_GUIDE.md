# 🚀 Backend API Setup Guide

Complete guide to set up and run the Raahi AI backend API server.

---

## 📋 Prerequisites

Before you start, ensure you have:

- ✅ Python 3.8 or higher installed
- ✅ PostgreSQL database running
- ✅ Database schema set up (from `database/postgresql/db_init.sql`)
- ✅ Location data loaded (138 locations in `location_mapping` table)
- ✅ POI data collected (optional but recommended)

---

## 🔧 Setup Steps

### 1. Install Dependencies

Navigate to backend_scripts directory:

```bash
cd backend_scripts
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- Flask-CORS (for mobile app integration)
- psycopg2 (PostgreSQL driver)
- All other dependencies

### 2. Update Database Schema

Run the schema update to add new itinerary columns:

**Option 1: Using pgAdmin**
1. Open pgAdmin
2. Connect to `raahi_ai` database
3. Open Query Tool
4. Open file: `database/postgresql/update_itinerary_schema.sql`
5. Execute (F5)

**Option 2: Using psql**
```bash
psql -U postgres -d raahi_ai -f ../database/postgresql/update_itinerary_schema.sql
```

Expected output:
```
✅ Itinerary table updated successfully!
📊 New columns added: daily_plan, total_cost, mood_tags, activities, travel_month
```

### 3. Configure Environment

Make sure your `.env` file exists in the project root (`E:\Raahi-AI\.env`):

```env
# Database Configuration
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=127.0.0.1
DB_PORT=5432

# API Configuration (optional)
PORT=5000

# POI Collection (optional - only if you want to collect POI data)
GEMINI_API_KEY=your_gemini_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

### 4. Test Database Connection

Before starting the server, test your database connection:

```bash
cd ..
python database/postgresql/connection.py
```

Expected output:
```
✅ Connected to PostgreSQL successfully!
📅 Server Time: 2025-12-10 10:00:00
```

If this fails, check:
- PostgreSQL is running
- Database `raahi_ai` exists
- Credentials in `.env` are correct

### 5. Verify POI Data (Optional but Recommended)

Check if you have POI data:

```sql
-- In pgAdmin Query Tool:
SELECT COUNT(*) FROM points_of_interest;
```

If you have 0 POIs:
```bash
# Collect POI data (takes 3-6 hours for all locations)
cd backend_scripts/api_collectors
python poi_pipeline.py --limit 3  # Start with 3 locations for testing

# Or collect all 138 locations
python poi_pipeline.py
```

**Note:** The API will work without POI data, but it won't be able to generate itineraries until you have some POIs in the database.

---

## 🎯 Running the Server

### Start the API Server

```bash
cd backend_scripts/api
python app.py
```

Expected output:
```
============================================================
🚀 Raahi AI Backend API Server
============================================================
📍 Running on: http://localhost:5000
📚 API Documentation: http://localhost:5000
============================================================

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Test the Server

Open your browser or use curl:

```bash
# Check if server is running
curl http://localhost:5000

# Health check
curl http://localhost:5000/api/health
```

You should see:
```json
{
  "name": "Raahi AI Backend API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {...}
}
```

---

## 🧪 Testing the API

### 1. Register a Test User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "test123"
  }'
```

Expected response:
```json
{
  "success": true,
  "user_id": 1,
  "message": "User registered successfully"
}
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'
```

### 3. Generate Test Itinerary

**Important:** Make sure you have POI data for the destination!

```bash
curl -X POST http://localhost:5000/api/itinerary/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "destination": "Hunza",
    "days": 3,
    "budget": 50000,
    "mood": ["adventurous"],
    "activities": ["hiking", "photography"],
    "travel_month": 5
  }'
```

Expected response:
```json
{
  "success": true,
  "itinerary_id": 1,
  "title": "3-Day Adventure Hunza Trip",
  "daily_plan": [...],
  ...
}
```

### 4. Get User's Itineraries

```bash
curl http://localhost:5000/api/itinerary/user/1
```

---

## 📁 Project Structure

```
backend_scripts/
├── api/
│   ├── __init__.py
│   ├── app.py                      # Main Flask application
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication endpoints
│   │   └── itinerary.py            # Itinerary endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── itinerary_generator.py  # Main generation algorithm
│   │   └── poi_matcher.py          # POI matching logic
│   ├── utils/
│   │   ├── __init__.py
│   │   └── db_helper.py            # Database utilities
│   ├── API_DOCUMENTATION.md        # Complete API docs
│   └── SETUP_GUIDE.md              # This file
├── api_collectors/                 # POI collection system
│   ├── poi_pipeline.py
│   ├── osm_collector.py
│   ├── llm_enricher.py
│   └── photo_fetcher.py
└── requirements.txt                # Python dependencies
```

---

## 🔍 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
cd backend_scripts
pip install -r requirements.txt
```

### Error: "Database connection failed"

**Solutions:**
1. Check if PostgreSQL is running
2. Verify `.env` file exists in project root
3. Test connection:
   ```bash
   python database/postgresql/connection.py
   ```

### Error: "No attractions found for this location"

**Solution:**
You need to collect POI data first:
```bash
cd backend_scripts/api_collectors
python poi_pipeline.py --limit 3
```

### Error: "Location 'XYZ' not found"

**Solutions:**
1. Check spelling of destination
2. Verify location exists:
   ```sql
   SELECT city FROM location_mapping WHERE verified = TRUE ORDER BY city;
   ```
3. Available destinations include: Hunza, Skardu, Gilgit, Naran, Kaghan, Murree, Swat, etc.

### Port 5000 Already in Use

**Solution:**
Change port in `.env`:
```env
PORT=5001
```

Or kill the process:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

---

## 🌐 Accessing from Mobile App

### Same Network (Development)

Find your computer's IP address:

**Windows:**
```bash
ipconfig
# Look for IPv4 Address (e.g., 192.168.1.10)
```

**Mac/Linux:**
```bash
ifconfig
# Look for inet address
```

Then in your mobile app, use:
```
http://192.168.1.10:5000/api/...
```

### Production Deployment

For production, deploy to:
- **Heroku** (free tier available)
- **AWS EC2**
- **Google Cloud Run**
- **DigitalOcean**
- **Railway**

---

## 🎨 Development Tips

### Run in Debug Mode

Flask automatically runs in debug mode, which provides:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger

### View Server Logs

All requests are logged to console. Watch for:
- Request method and path
- Response status code
- Errors (if any)

### Testing with Postman

1. Download Postman
2. Import the following collection:
   - Base URL: `http://localhost:5000`
   - Create requests for each endpoint
   - Save as collection for reuse

---

## 📊 Performance Optimization

### Database Indexes

Already created for fast queries:
- `idx_poi_location_id` - Fast POI lookup by location
- `idx_poi_mood_tags` - Fast mood filtering (GIN index)
- `idx_poi_activities` - Fast activity filtering (GIN index)
- `idx_itineraries_user_id` - Fast user itinerary lookup

### API Response Time

Expected response times:
- Authentication: <100ms
- Get itinerary: <200ms
- Generate itinerary: 1-3 seconds (depends on POI count)

---

## 🔒 Security Notes

### Current Implementation

- Passwords are hashed using SHA256
- No authentication tokens (for simplicity)
- CORS enabled for all origins

### For Production

Consider adding:
- JWT tokens for authentication
- Password hashing with bcrypt + salt
- Rate limiting
- HTTPS only
- API key authentication
- Input validation and sanitization

---

## 🎉 You're Ready!

Your backend API is now set up and running!

**Next Steps:**
1. ✅ Test all endpoints
2. ✅ Collect POI data for your target destinations
3. ✅ Integrate with mobile app
4. ✅ Deploy to production (when ready)

**For API usage details, see:** `API_DOCUMENTATION.md`

**Happy coding! 🚀**

