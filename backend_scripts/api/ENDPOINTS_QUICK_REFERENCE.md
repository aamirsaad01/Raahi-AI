# ⚡ API Endpoints Quick Reference

Quick copy-paste reference for all endpoints.

---

## 🔑 Authentication

### Register
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Ali Khan","email":"ali@example.com","password":"test123"}'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ali@example.com","password":"test123"}'
```

---

## 🗺️ Itinerary - Recommendation Flow (NEW!)

### 1. Get Recommendations (no destination needed!)
```bash
curl -X POST http://localhost:5000/api/itinerary/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 50000,
    "mood": ["adventurous", "romantic"],
    "activities": ["hiking", "photography"],
    "days": 3,
    "travel_month": 5,
    "num_recommendations": 5
  }'
```

**Response:** 5 destinations with photos, highlights, and costs

### 2. Generate Full Itinerary (after user selects)
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

**Response:** Complete day-by-day itinerary

---

## 🗺️ Itinerary - Direct Generation (Alternative)

### Generate Without Recommendations
```bash
curl -X POST http://localhost:5000/api/itinerary/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "destination": "Skardu",
    "days": 5,
    "budget": 75000,
    "mood": ["adventurous", "cultural"],
    "activities": ["trekking", "photography"],
    "travel_month": 6
  }'
```

---

## 📋 Itinerary Management

### Get Itinerary by ID
```bash
curl http://localhost:5000/api/itinerary/123
```

### Get User's All Itineraries
```bash
curl http://localhost:5000/api/itinerary/user/1
```

### Update Itinerary
```bash
curl -X PUT http://localhost:5000/api/itinerary/123 \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Title","budget":60000}'
```

### Delete Itinerary
```bash
curl -X DELETE http://localhost:5000/api/itinerary/123
```

---

## 🏥 Health Check

```bash
curl http://localhost:5000/api/health
```

---

## 📱 Mobile App (Flutter)

### Recommended Flow

```dart
// 1. Get recommendations
final recResponse = await http.post(
  Uri.parse('$baseUrl/api/itinerary/recommend'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'budget': 50000,
    'mood': ['adventurous'],
    'days': 3,
  }),
);

// 2. Display options with photos
// (User selects one)

// 3. Generate full itinerary
final genResponse = await http.post(
  Uri.parse('$baseUrl/api/itinerary/generate'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_id': userId,
    'destination': selectedDestination,
    'budget': 50000,
    'mood': ['adventurous'],
    'days': 3,
  }),
);
```

---

## 🎯 Mood Options

```
adventurous
romantic
family
cultural
relaxed
```

---

## 🎯 Activity Options

```
hiking
photography
camping
skiing
boating
sightseeing
trekking
fishing
```

---

## 🌍 Popular Destinations

```
Hunza, Skardu, Gilgit, Naran, Kaghan, Murree, Swat, 
Chitral, Fairy Meadows, Astore, Shigar, Khunjerab Pass,
Deosai Plains, Neelum Valley, Shogran, and 120+ more!
```

---

## 🔧 Configuration

**Development:**
```
Base URL: http://localhost:5000
```

**Production:**
```
Base URL: https://your-api.herokuapp.com
```

---

## 📊 Response Codes

```
200 OK              - Success
201 Created         - Resource created
400 Bad Request     - Invalid input
401 Unauthorized    - Invalid credentials
404 Not Found       - Resource not found
500 Server Error    - Internal error
```

---

## 🎉 That's It!

**Full docs:** See `API_DOCUMENTATION.md`
**Mobile guide:** See `MOBILE_APP_INTEGRATION.md`

