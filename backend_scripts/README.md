# 🔧 Raahi AI - Backend System

Complete backend system for itinerary generation, POI collection, and packing checklists.

---

## 📦 What's Included

### 1. **REST API Server** (NEW!)
Complete Flask API for itinerary generation and management.

**Location:** `api/`

**Features:**
- ✅ User authentication (register/login)
- ✅ AI-powered itinerary generation
- ✅ POI matching algorithm
- ✅ Budget optimization
- ✅ Day-by-day scheduling
- ✅ CRUD operations for itineraries

**Quick Start:**
```bash
cd api
python app.py
```

📚 **Documentation:** `api/API_DOCUMENTATION.md`  
🔧 **Setup Guide:** `api/SETUP_GUIDE.md`

---

### 2. **POI Collection System**
Automated system to collect Points of Interest data using free APIs.

**Location:** `api_collectors/`

**Features:**
- ✅ Fetch POIs from OpenStreetMap (free)
- ✅ Enrich with Google Gemini LLM (free)
- ✅ Fetch photos from Unsplash (optional, free)
- ✅ Store in PostgreSQL with rich metadata

**Quick Start:**
```bash
cd api_collectors
python poi_pipeline.py --limit 3  # Test with 3 locations
python poi_pipeline.py            # Collect all 138 locations
```

📚 **Documentation:** `POI_COLLECTION_GUIDE.md`  
🔑 **API Keys Setup:** `CREDENTIALS_SETUP.md`

---

### 3. **Checklist Generator**
Smart packing list generator based on location and activities.

**Location:** `checklist_generator.py`

**Features:**
- ✅ Climate-based recommendations
- ✅ Activity-specific gear
- ✅ Location-aware essentials
- ✅ Month-based clothing suggestions

**Usage:**
```python
from checklist_generator import ChecklistGenerator

generator = ChecklistGenerator()
checklist = generator.generate_checklist(
    area="Hunza",
    region="Gilgit-Baltistan",
    month=5,
    activities=["hiking", "photography"]
)
print(checklist)
```

---

## 🗄️ Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts |
| `location_mapping` | 138 locations with coordinates |
| `points_of_interest` | Tourist attractions with AI metadata |
| `itineraries` | Generated travel plans |
| `checklist` | Packing lists |
| `hazard_reports` | Safety reports |

### Key Features
- ✅ JSONB support for flexible data
- ✅ GIN indexes for fast filtering
- ✅ Foreign key constraints
- ✅ Automatic timestamps

**Schema Files:**
- `../database/postgresql/db_init.sql` - Initial schema
- `../database/postgresql/update_itinerary_schema.sql` - Itinerary updates

---

## 🚀 Complete Setup

### Prerequisites

1. **Python 3.8+**
2. **PostgreSQL** (with `raahi_ai` database)
3. **Environment Variables** (`.env` file in project root)

### Step-by-Step Setup

```bash
# 1. Install dependencies
cd backend_scripts
pip install -r requirements.txt

# 2. Update database schema
# Run in pgAdmin: database/postgresql/update_itinerary_schema.sql

# 3. (Optional) Collect POI data
cd api_collectors
python poi_pipeline.py --limit 3

# 4. Start API server
cd ../api
python app.py

# 5. Test the API
curl http://localhost:5000/api/health
```

---

## 📚 Documentation Files

| File | Description |
|------|-------------|
| `api/API_DOCUMENTATION.md` | Complete API reference with examples |
| `api/SETUP_GUIDE.md` | Detailed setup instructions |
| `POI_COLLECTION_GUIDE.md` | How to collect POI data |
| `CREDENTIALS_SETUP.md` | How to get free API keys |
| `IMPLEMENTATION_SUMMARY.md` | Project overview |

---

## 🎯 Common Use Cases

### Use Case 1: Generate Itinerary

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

### Use Case 2: Collect POI Data

```bash
cd api_collectors
python poi_pipeline.py --limit 10  # Process 10 locations
python poi_pipeline.py --stats     # View statistics
```

### Use Case 3: Generate Packing List

```python
from checklist_generator import ChecklistGenerator

with ChecklistGenerator() as gen:
    result = gen.generate_checklist(
        area="Skardu",
        region="Gilgit-Baltistan",
        month=6,
        activities=["trekking", "camping"]
    )
    print(result)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                Mobile App (Flutter)                 │
│                                                     │
│   • Itinerary Generation UI                        │
│   • POI Display                                    │
│   • User Authentication                            │
└─────────────┬───────────────────────────────────────┘
              │ HTTP/REST
              ▼
┌─────────────────────────────────────────────────────┐
│            Flask Backend API (api/)                 │
│                                                     │
│   Routes:      Services:           Utils:          │
│   • auth.py    • itinerary_       • db_helper.py   │
│   • itinerary   generator.py                       │
│                • poi_matcher.py                     │
└─────────────┬───────────────────────────────────────┘
              │ SQL
              ▼
┌─────────────────────────────────────────────────────┐
│         PostgreSQL Database (raahi_ai)              │
│                                                     │
│   • users                  • points_of_interest    │
│   • location_mapping       • itineraries           │
│   • checklist             • hazard_reports         │
└─────────────────────────────────────────────────────┘
              ▲
              │ Data Collection
┌─────────────┴───────────────────────────────────────┐
│        POI Collection Pipeline                      │
│                                                     │
│   1. OpenStreetMap → Raw POI data                  │
│   2. Google Gemini → AI enrichment                 │
│   3. Unsplash → Photos                             │
└─────────────────────────────────────────────────────┘
```

---

## 🧪 Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"test123"}'

# Generate itinerary (requires POI data!)
curl -X POST http://localhost:5000/api/itinerary/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"destination":"Hunza","days":3,"budget":50000,"mood":["adventurous"],"activities":["hiking"],"travel_month":5}'
```

### Test POI System

```bash
cd api_collectors
python test_poi_system.py
```

### Test Database Connection

```bash
python ../database/postgresql/connection.py
```

---

## 📊 Data Collection Progress

Check your POI data:

```bash
cd api_collectors
python poi_pipeline.py --stats
```

Expected output:
```
📊 POI DATABASE STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total POIs: 847
Average Rating: 4.2/5.0

POIs by Category:
  nature         : 512
  cultural       :  98
  adventure      :  87
  religious      :  76
  historical     :  74

POIs by Region:
  Gilgit-Baltistan    : 412
  KPK Highlands       : 198
  Hazara Division     : 156
```

---

## 🔧 Configuration

### Environment Variables (`.env`)

```env
# Database
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

# API Server
PORT=5000

# POI Collection (optional)
GEMINI_API_KEY=your_gemini_key
UNSPLASH_ACCESS_KEY=your_unsplash_key
```

---

## 💰 Cost Breakdown

```
PostgreSQL:        $0.00 (local)
Flask Server:      $0.00 (local)
OpenStreetMap:     $0.00 (unlimited free)
Google Gemini:     $0.00 (free tier - 60 req/min)
Unsplash:          $0.00 (free tier - 50 req/hour)
────────────────────────────────────────
TOTAL:             $0.00 ✅
```

**Everything is FREE!** 🎉

---

## 🚀 Deployment Options

### Development
- Run locally: `python api/app.py`
- Access from mobile: `http://your-ip:5000`

### Production

**Recommended Platforms:**
1. **Heroku** - Easy deployment, free tier
2. **Railway** - Modern, generous free tier
3. **Render** - Simple deployment
4. **AWS EC2** - Full control
5. **Google Cloud Run** - Serverless

**Deployment Guide:** See `api/SETUP_GUIDE.md`

---

## 📱 Mobile App Integration

Your Flutter app should make API calls to:

```dart
final baseUrl = 'http://your-server:5000';

// Generate itinerary
final response = await http.post(
  Uri.parse('$baseUrl/api/itinerary/generate'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_id': userId,
    'destination': 'Hunza',
    'days': 3,
    'budget': 50000,
    'mood': ['adventurous'],
    'activities': ['hiking'],
  }),
);
```

---

## 🔍 Troubleshooting

### Common Issues

**1. "No attractions found"**
- Solution: Collect POI data first
- Run: `cd api_collectors && python poi_pipeline.py --limit 3`

**2. "Database connection failed"**
- Check PostgreSQL is running
- Verify `.env` file exists and has correct credentials

**3. "Import errors"**
- Run: `pip install -r requirements.txt`

**4. "Port already in use"**
- Change PORT in `.env`
- Or kill existing process

---

## 📖 Learning Resources

1. **Flask Documentation:** https://flask.palletsprojects.com/
2. **PostgreSQL JSONB:** https://www.postgresql.org/docs/current/datatype-json.html
3. **Google Gemini API:** https://ai.google.dev/
4. **OpenStreetMap Overpass:** https://wiki.openstreetmap.org/wiki/Overpass_API

---

## 🎯 Next Steps

### For Backend Development:
1. ✅ Review API documentation
2. ✅ Test all endpoints
3. ✅ Collect POI data for target locations
4. ✅ Deploy to production server

### For Frontend Integration:
1. ✅ Get API base URL
2. ✅ Implement authentication flow
3. ✅ Call itinerary generation endpoint
4. ✅ Display results in mobile app

---

## 📂 File Structure

```
backend_scripts/
├── api/                            # REST API Server (NEW!)
│   ├── app.py                      # Main Flask app
│   ├── routes/                     # API endpoints
│   │   ├── auth.py
│   │   └── itinerary.py
│   ├── services/                   # Business logic
│   │   ├── itinerary_generator.py
│   │   └── poi_matcher.py
│   ├── utils/                      # Utilities
│   │   └── db_helper.py
│   ├── API_DOCUMENTATION.md        # API reference
│   └── SETUP_GUIDE.md              # Setup instructions
│
├── api_collectors/                 # POI Collection System
│   ├── poi_pipeline.py             # Main orchestrator
│   ├── osm_collector.py            # OpenStreetMap fetcher
│   ├── llm_enricher.py             # Gemini AI enrichment
│   └── photo_fetcher.py            # Unsplash photos
│
├── checklist_generator.py          # Packing list generator
├── test_poi_system.py              # System tests
├── requirements.txt                # Python dependencies
├── POI_COLLECTION_GUIDE.md         # POI guide
├── CREDENTIALS_SETUP.md            # API keys guide
└── README.md                       # This file
```

---

## 🎉 You're All Set!

Your complete backend system is ready:
- ✅ REST API for mobile app
- ✅ POI collection pipeline
- ✅ Itinerary generation algorithm
- ✅ Packing checklist system
- ✅ Complete documentation

**Start the server and begin building! 🚀**

For questions or issues, refer to the documentation files or check the code comments.

**Happy coding!**

