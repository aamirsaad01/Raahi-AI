# 🚀 Frontend Developer Setup Guide

Complete guide to set up and run the Raahi AI backend API on your laptop.

---

## 📋 Prerequisites

Before starting, make sure you have:

- ✅ **Python 3.8 or higher** installed
- ✅ **PostgreSQL** installed and running
- ✅ **Git** installed
- ✅ **Internet connection** (for API calls)

---

## 🔧 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/aamirsaad01/Raahi-AI.git
cd Raahi-AI
```

---

### Step 2: Install PostgreSQL (if not installed)

**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- Install with default settings
- Remember the password you set for `postgres` user

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

---

### Step 3: Create Database

**Option A: Using pgAdmin (Recommended - GUI)**

1. Open **pgAdmin 4** (installed with PostgreSQL)
2. Connect to PostgreSQL server (use password you set during installation)
3. Right-click on **Databases** → **Create** → **Database**
4. Name: `raahi_ai`
5. Click **Save**

**Option B: Using Command Line**

```bash
# Windows (PowerShell)
psql -U postgres
CREATE DATABASE raahi_ai;
\q

# Mac/Linux
sudo -u postgres psql
CREATE DATABASE raahi_ai;
\q
```

---

### Step 4: Run Database Schema

**Using pgAdmin:**
1. Right-click on `raahi_ai` database → **Query Tool**
2. Open file: `database/postgresql/db_init.sql`
3. Press **F5** (Execute)
4. Wait for "Success" message

**Using Command Line:**
```bash
# Windows
psql -U postgres -d raahi_ai -f database/postgresql/db_init.sql

# Mac/Linux
psql -U postgres -d raahi_ai -f database/postgresql/db_init.sql
```

---

### Step 5: Update Database Schema (Important!)

**Using pgAdmin:**
1. Right-click on `raahi_ai` database → **Query Tool**
2. Open file: `database/postgresql/update_itinerary_schema.sql`
3. Press **F5** (Execute)
4. You should see: "✅ Itinerary table updated successfully!"

**Using Command Line:**
```bash
psql -U postgres -d raahi_ai -f database/postgresql/update_itinerary_schema.sql
```

---

### Step 6: Load Location Data

```bash
cd database
python load_location_data.py
```

This loads 138 locations into the database.

**Expected output:**
```
✅ Connected to database
✅ Loaded 138 locations
```

---

### Step 7: Install Python Dependencies

```bash
cd backend_scripts
pip install -r requirements.txt
```

**If you get permission errors:**
```bash
# Windows
python -m pip install -r requirements.txt

# Mac/Linux
pip3 install -r requirements.txt
```

---

### Step 8: Configure Environment Variables

1. Create `.env` file in the **project root** (`Raahi-AI/.env`):

```env
# Database Configuration
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
DB_HOST=127.0.0.1
DB_PORT=5432

# API Keys (Optional - for POI data collection)
# Get from: https://makersuite.google.com/app/apikey (Gemini)
# Get from: https://unsplash.com/developers (Unsplash)
GEMINI_API_KEY=your_gemini_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

**Important:** Replace `your_postgres_password_here` with your actual PostgreSQL password!

**Note:** API keys are optional. The system works without them, but POI data collection will be limited.

---

### Step 9: Test Database Connection

```bash
cd database
python postgresql/connection.py
```

**Expected output:**
```
✅ Connected to database successfully!
Database: raahi_ai
```

If you get an error, check your `.env` file credentials.

---

### Step 10: Collect POI Data (Optional but Recommended)

To generate itineraries, you need POI (Points of Interest) data in the database.

**Quick Test (3 locations - takes ~10 minutes):**
```bash
cd backend_scripts/api_collectors
python poi_pipeline.py --limit 3
```

**Full Collection (all locations - takes ~2-3 hours):**
```bash
python poi_pipeline.py
```

**Expected output:**
```
✅ Processing location: Hunza
✅ Collected 5 POIs
✅ Enriched with LLM
✅ Fetched photos
...
```

**Note:** This step requires API keys. If you don't have them, the system will use default data, but it's better to have real POI data.

---

### Step 11: Start the Backend Server

**Windows:**
```bash
cd backend_scripts/api
run_server.bat
```

**Mac/Linux:**
```bash
cd backend_scripts/api
chmod +x run_server.sh
./run_server.sh
```

**Or manually:**
```bash
cd backend_scripts/api
python app.py
```

**Expected output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

✅ **Server is running!**

---

### Step 12: Test the API

Open your browser: `http://localhost:5000`

You should see:
```json
{
  "name": "Raahi AI Backend API",
  "version": "1.0.0",
  "status": "running"
}
```

**Test with curl:**
```bash
curl http://localhost:5000/api/health
```

---

### Step 13: Connect Your Frontend

**For Local Development:**

Update your frontend API base URL to:
```dart
// Flutter example
final String apiBaseUrl = 'http://localhost:5000';
```

**For Mobile Testing (Phone/Emulator):**

1. Find your computer's IP address:
   - **Windows:** `ipconfig` (look for IPv4 Address)
   - **Mac/Linux:** `ifconfig` (look for inet)

2. Update frontend API base URL:
```dart
final String apiBaseUrl = 'http://192.168.1.10:5000'; // Replace with your IP
```

3. Make sure your firewall allows port 5000

---

## 🧪 Quick Test: Generate an Itinerary

Once everything is set up, test the itinerary generation:

```bash
# Register a user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@test.com","password":"test123"}'

# Generate itinerary
curl -X POST http://localhost:5000/api/itinerary/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "destination": "Hunza",
    "days": 3,
    "budget": 50000,
    "mood": ["adventurous"],
    "activities": ["hiking"],
    "travel_month": 5
  }'
```

---

## 📱 Frontend Integration

### API Endpoints You'll Use

**Base URL:** `http://localhost:5000` (or your IP for mobile)

1. **Register User:**
   ```
   POST /api/auth/register
   Body: { "name": "...", "email": "...", "password": "..." }
   ```

2. **Login:**
   ```
   POST /api/auth/login
   Body: { "email": "...", "password": "..." }
   ```

3. **Get Recommendations:**
   ```
   POST /api/itinerary/recommend
   Body: { "budget": 50000, "mood": ["adventurous"], "days": 3, ... }
   ```

4. **Generate Itinerary:**
   ```
   POST /api/itinerary/generate
   Body: { "user_id": 1, "destination": "Hunza", "days": 3, ... }
   ```

**Full API Documentation:** See `backend_scripts/api/API_DOCUMENTATION.md`

---

## 🐛 Troubleshooting

### Server won't start

**Error:** `ModuleNotFoundError: No module named 'flask'`
- **Solution:** Run `pip install -r backend_scripts/requirements.txt`

**Error:** `Connection refused` or database errors
- **Solution:** Check PostgreSQL is running
- **Solution:** Verify `.env` file has correct database credentials

### Database connection fails

**Error:** `FATAL: password authentication failed`
- **Solution:** Check `DB_PASSWORD` in `.env` matches your PostgreSQL password

**Error:** `FATAL: database "raahi_ai" does not exist`
- **Solution:** Create database (Step 3)

### Itinerary generation fails

**Error:** `No attractions found`
- **Solution:** Collect POI data (Step 10)

**Error:** `column "daily_plan" does not exist`
- **Solution:** Run `update_itinerary_schema.sql` (Step 5)

### Frontend can't connect

**Error:** CORS errors or connection refused
- **Solution:** Use your computer's IP address (not localhost) for mobile testing
- **Solution:** Check firewall allows port 5000
- **Solution:** Verify server is running

---

## 📚 Additional Resources

- **API Documentation:** `backend_scripts/api/API_DOCUMENTATION.md`
- **Quick Start:** `backend_scripts/api/QUICK_START.md`
- **Mobile Integration:** `backend_scripts/api/MOBILE_APP_INTEGRATION.md`
- **POI Collection:** `backend_scripts/POI_COLLECTION_GUIDE.md`

---

## ✅ Checklist

Before connecting your frontend, make sure:

- [ ] PostgreSQL is installed and running
- [ ] Database `raahi_ai` is created
- [ ] Database schema is initialized (`db_init.sql`)
- [ ] Database schema is updated (`update_itinerary_schema.sql`)
- [ ] Location data is loaded (138 locations)
- [ ] Python dependencies are installed
- [ ] `.env` file is configured with correct credentials
- [ ] POI data is collected (optional but recommended)
- [ ] Backend server is running on port 5000
- [ ] Health check works: `http://localhost:5000/api/health`

---

## 🎉 You're Ready!

Once all steps are complete, your backend API is ready to use with your frontend!

**Server URL:** `http://localhost:5000`

**Need Help?** Check the troubleshooting section or review the detailed documentation files.

---

**Happy Coding! 🚀**

