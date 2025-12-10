# ⚡ Quick Start Guide

Get the backend API running in 5 minutes!

---

## 🚀 Super Quick Setup

### 1. Update Database (30 seconds)

Open pgAdmin → Query Tool → Run this file:
```
database/postgresql/update_itinerary_schema.sql
```

### 2. Install Dependencies (2 minutes)

```bash
cd backend_scripts
pip install -r requirements.txt
```

### 3. Start Server (instantly!)

**Windows:**
```bash
cd api
run_server.bat
```

**Mac/Linux:**
```bash
cd api
chmod +x run_server.sh
./run_server.sh
```

**Or manually:**
```bash
cd api
python app.py
```

### 4. Test It! (30 seconds)

Open browser: http://localhost:5000

You should see:
```json
{
  "name": "Raahi AI Backend API",
  "version": "1.0.0",
  "status": "running"
}
```

✅ **Done! API is running!**

---

## 🧪 Quick Test

### Test Health:
```bash
curl http://localhost:5000/api/health
```

### Register User:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test\",\"email\":\"test@test.com\",\"password\":\"test123\"}"
```

### Generate Itinerary (needs POI data):
```bash
curl -X POST http://localhost:5000/api/itinerary/generate \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":1,\"destination\":\"Hunza\",\"days\":3,\"budget\":50000,\"mood\":[\"adventurous\"],\"activities\":[\"hiking\"],\"travel_month\":5}"
```

---

## ⚠️ Important!

### If Itinerary Generation Fails:

**Error:** "No attractions found"

**Solution:** You need POI data!

```bash
cd ../api_collectors
python poi_pipeline.py --limit 3
```

This takes ~10 minutes for 3 locations.

---

## 📱 For Mobile App

Your mobile app should call:

**Base URL:** `http://your-ip-address:5000`

**Find your IP:**
- Windows: `ipconfig`
- Mac/Linux: `ifconfig`

**Example from mobile:**
```dart
final response = await http.post(
  Uri.parse('http://192.168.1.10:5000/api/itinerary/generate'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({...}),
);
```

---

## 🔥 Pro Tips

### Keep Server Running:
Leave the terminal open with the server running

### View Logs:
All requests are logged in the terminal

### Auto-Reload:
Code changes automatically reload (debug mode)

### Stop Server:
Press `Ctrl + C`

---

## 📚 Full Documentation

For detailed docs, see:
- `API_DOCUMENTATION.md` - Complete API reference
- `SETUP_GUIDE.md` - Detailed setup
- `../README.md` - Backend overview

---

## 🎯 That's It!

You now have a fully functional backend API! 🎉

**Next:** Share the API URL with your frontend developer!

