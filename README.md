# 🗺️ Raahi AI - Travel Itinerary Generator

AI-powered travel itinerary generation system for Pakistan. Complete backend API with Flutter mobile app.

---

## 📁 Project Structure

```
Raahi-AI/
├── backend_scripts/          # Python backend
│   ├── api/                  # REST API server (Flask)
│   ├── api_collectors/       # POI data collection system
│   └── data/                 # CSV data files
├── database/                 # PostgreSQL setup
│   └── postgresql/           # SQL scripts
└── mobile_app/               # Flutter mobile application
```

---

## 🚀 Quick Start

### For Frontend Developers (First Time Setup)

**👉 Start here:** See [`FRONTEND_DEVELOPER_SETUP.md`](FRONTEND_DEVELOPER_SETUP.md) for complete step-by-step instructions.

### Backend Setup (Quick Reference)

1. **Database Setup:**
   - Install PostgreSQL
   - Create database: `raahi_ai`
   - Run: `database/postgresql/db_init.sql`
   - Run: `database/postgresql/update_itinerary_schema.sql`

2. **Environment Variables:**
   - Create `.env` file in project root
   - Fill in database credentials
   - Add API keys (optional): `GEMINI_API_KEY`, `UNSPLASH_ACCESS_KEY`

3. **Install Dependencies:**
   ```bash
   cd backend_scripts
   pip install -r requirements.txt
   ```

4. **Start Server:**
   ```bash
   cd backend_scripts/api
   python app.py
   ```
   Server runs on: `http://localhost:5000`

### Mobile App Setup

```bash
cd mobile_app
flutter pub get
flutter run
```

---

## 📡 API Endpoints

**Base URL:** `http://localhost:5000`

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login

### Itinerary
- `POST /api/itinerary/recommend` - Get destination recommendations
- `POST /api/itinerary/generate` - Generate full itinerary
- `GET /api/itinerary/{id}` - Get itinerary details
- `GET /api/itinerary/user/{user_id}` - Get user's itineraries
- `PUT /api/itinerary/{id}` - Update itinerary
- `DELETE /api/itinerary/{id}` - Delete itinerary

### Health
- `GET /api/health` - Health check

**Full API Documentation:** See `backend_scripts/api/API_DOCUMENTATION.md`

---

## 📚 Documentation

- **⭐ Frontend Developer Setup:** [`FRONTEND_DEVELOPER_SETUP.md`](FRONTEND_DEVELOPER_SETUP.md) - **Start here if you're setting up for the first time!**
- **Backend API:** `backend_scripts/api/API_DOCUMENTATION.md`
- **Quick Start:** `backend_scripts/api/QUICK_START.md`
- **Setup Guide:** `backend_scripts/api/SETUP_GUIDE.md`
- **Mobile Integration:** `backend_scripts/api/MOBILE_APP_INTEGRATION.md`
- **Database Setup:** `database/README.md`
- **POI Collection:** `backend_scripts/POI_COLLECTION_GUIDE.md`

---

## 🛠️ Tech Stack

**Backend:**
- Python 3.8+
- Flask (REST API)
- PostgreSQL
- Google Gemini (LLM enrichment)
- OpenStreetMap (POI data)
- Unsplash (Photos)

**Mobile:**
- Flutter/Dart
- Material Design

---

## 🔑 Environment Variables

Create `.env` file in project root:

```env
# Database
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

# API Keys (Optional)
GEMINI_API_KEY=your_gemini_key
UNSPLASH_ACCESS_KEY=your_unsplash_key
```

---

## 📝 Features

- ✅ AI-powered destination recommendations
- ✅ Personalized itinerary generation
- ✅ POI matching based on mood & activities
- ✅ Budget optimization
- ✅ Season-aware recommendations
- ✅ Day-by-day scheduling
- ✅ Cost breakdown
- ✅ User authentication
- ✅ Mobile app ready (CORS enabled)

---

## 🤝 For Frontend Developers

### API Base URL
- **Local:** `http://localhost:5000`
- **Network:** `http://YOUR_IP:5000` (for mobile testing)

### Example Request (Generate Itinerary)

```json
POST /api/itinerary/generate
Content-Type: application/json

{
  "user_id": 1,
  "destination": "Hunza",
  "days": 3,
  "budget": 50000,
  "mood": ["adventurous", "romantic"],
  "activities": ["hiking", "photography"],
  "travel_month": 5
}
```

### Example Response

```json
{
  "success": true,
  "itinerary_id": 1,
  "title": "3-Day Adventure Hunza Trip",
  "destination": "Hunza",
  "days": 3,
  "total_budget": 50000,
  "cost_breakdown": {
    "total_estimated": 47000,
    "breakdown": {
      "attractions": 12000,
      "accommodation": 20000,
      "food": 10000,
      "transport": 5000
    }
  },
  "daily_plan": [
    {
      "day": 1,
      "date": "2025-12-10",
      "pois": [...],
      "total_duration_hours": 8.0,
      "estimated_cost": 8000
    }
  ]
}
```

**Full API Reference:** `backend_scripts/api/API_DOCUMENTATION.md`

---

## 📦 Data Collection

To collect POI data for locations:

```bash
cd backend_scripts/api_collectors
python poi_pipeline.py --limit 10
```

This collects POIs from OpenStreetMap, enriches with LLM, and fetches photos.

**Guide:** `backend_scripts/POI_COLLECTION_GUIDE.md`

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Register User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"test123"}'
```

---

## 📄 License

[Your License Here]

---

## 👥 Contributors

- Backend: [Your Name]
- Frontend: [Friend's Name]

---

## 🐛 Troubleshooting

**Server won't start:**
- Check PostgreSQL is running
- Verify `.env` file exists with correct credentials
- Check port 5000 is not in use

**Itinerary generation fails:**
- Ensure database schema is updated (`update_itinerary_schema.sql`)
- Check POI data exists in database
- Verify location name spelling

**Mobile app can't connect:**
- Use your computer's IP address (not localhost)
- Check firewall allows port 5000
- Verify CORS is enabled (it is by default)

---

**For detailed setup instructions, see:** `backend_scripts/api/SETUP_GUIDE.md`
