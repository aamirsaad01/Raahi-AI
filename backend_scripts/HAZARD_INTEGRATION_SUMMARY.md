# 🚨 Hazard Map Feature - Backend Integration Summary

## ✅ Integration Complete

The hazard map feature has been fully integrated with the backend API. Here's what was implemented:

## 📋 What Was Done

### Backend (Flask API)

1. **New API Endpoints** (`backend_scripts/api.py`):
   - `GET /api/hazards` - Get all hazards (NDMA alerts + user reports)
     - Query params: `source` (ndma/user/pmd), `severity`, `time_window` (24h/7d/1m/all)
   - `POST /api/hazards/report` - Submit new user hazard report
   - `GET /api/hazards/my-reports` - Get user's reported hazards

2. **NDMA Alert Mapping**:
   - Automatically converts NDMA advisories to hazard reports
   - Extracts location coordinates from affected regions
   - Maps advisory types to hazard types (landslide, flood, etc.)
   - Preserves severity classification

### Frontend (Flutter)

1. **API Service** (`mobile_app/lib/features/hazard/api_service.dart`):
   - `HazardApiService` class for all API calls
   - Handles JSON serialization/deserialization
   - Error handling

2. **Updated Models** (`mobile_app/lib/features/hazard/models.dart`):
   - Added `fromJson()` and `toJson()` methods
   - Added `advisoryUrl` and `advisoryType` fields for NDMA alerts

3. **Updated Pages**:
   - **Hazard Map Page**: Now loads real data from API with filters
   - **Report Hazard Page**: Submits to backend API
   - **My Reports Page**: Loads user reports from API
   - **Layers & Filters Sheet**: Functional filters with callbacks

## 🔌 API Endpoints

### Get Hazards
```
GET /api/hazards?source=ndma&severity=high&time_window=7d
```

**Response:**
```json
{
  "success": true,
  "hazards": [
    {
      "id": "ndma_1",
      "type": "landslide",
      "severity": "high",
      "timestamp": "2025-12-08T12:00:00Z",
      "source": "NDMA",
      "lat": 35.9208,
      "lon": 74.3089,
      "location": "Karimabad",
      "description": "Landslide advisory...",
      "advisory_url": "http://...",
      "advisory_type": "Landslide Alert"
    }
  ],
  "count": 1
}
```

### Report Hazard
```
POST /api/hazards/report
Content-Type: application/json

{
  "type": "roadblock",
  "severity": "medium",
  "location": "Karimabad, Hunza",
  "lat": 35.9208,
  "lon": 74.3089,
  "description": "Road blocked due to construction"
}
```

**Response:**
```json
{
  "success": true,
  "hazard_id": 123,
  "reported_at": "2025-12-08T12:00:00Z",
  "message": "Hazard reported successfully"
}
```

### Get My Reports
```
GET /api/hazards/my-reports
```

**Response:** Same format as Get Hazards

## 🧪 Testing

### 1. Start Backend Server

```bash
cd backend_scripts
python api.py
```

Server runs on `http://127.0.0.1:5000`

### 2. Test API Endpoints

**Get all hazards:**
```bash
curl http://127.0.0.1:5000/api/hazards
```

**Get NDMA alerts only:**
```bash
curl http://127.0.0.1:5000/api/hazards?source=ndma
```

**Report a hazard:**
```bash
curl -X POST http://127.0.0.1:5000/api/hazards/report \
  -H "Content-Type: application/json" \
  -d '{
    "type": "roadblock",
    "severity": "medium",
    "location": "Test Location",
    "lat": 35.9208,
    "lon": 74.3089,
    "description": "Test hazard"
  }'
```

### 3. Test Flutter App

1. **Update API URL** (if needed):
   - For Android emulator: Change `baseUrl` in `api_service.dart` to `http://10.0.2.2:5000`
   - For iOS simulator: Use `http://localhost:5000`
   - For physical device: Use your computer's IP address

2. **Run Flutter app:**
   ```bash
   cd mobile_app
   flutter run
   ```

3. **Test features:**
   - Navigate to Hazard Map
   - Should see NDMA alerts from database
   - Try filters (source, severity, time window)
   - Report a new hazard
   - Check "My Reports" page

## 🔧 Configuration

### Backend API URL

In `mobile_app/lib/features/hazard/api_service.dart`:
```dart
static const String baseUrl = 'http://127.0.0.1:5000';
```

Change this based on your setup:
- **Local testing**: `http://127.0.0.1:5000`
- **Android emulator**: `http://10.0.2.2:5000`
- **iOS simulator**: `http://localhost:5000`
- **Physical device**: `http://YOUR_COMPUTER_IP:5000`

## 📊 Data Flow

1. **NDMA Poller** → Scrapes NDMA website → Saves to `ndma_alerts` table
2. **Flutter App** → Calls `/api/hazards` → Backend queries `ndma_alerts` + `hazard_reports`
3. **Backend** → Maps NDMA alerts to hazard format → Returns JSON
4. **Flutter App** → Displays hazards on map/list

## 🎯 Features

✅ Real-time NDMA alerts from database
✅ User-reported hazards
✅ Filtering by source (NDMA/User/PMD)
✅ Filtering by severity
✅ Time window filtering (24h/7d/1m/all)
✅ Pull-to-refresh
✅ Error handling
✅ Loading states
✅ Empty states

## 🐛 Troubleshooting

### "Network error" in Flutter
- Check backend server is running
- Verify API URL is correct
- Check firewall/network settings
- For Android emulator, use `10.0.2.2:5000`

### No hazards showing
- Check if NDMA poller has run: `python backend_scripts/ndma_poller.py --once`
- Check database: `SELECT COUNT(*) FROM ndma_alerts;`
- Check backend logs for errors

### Can't submit hazard report
- Check database connection in backend
- Verify `hazard_reports` table exists
- Check backend logs for errors

## 📝 Next Steps

- [ ] Add map view (currently list view)
- [ ] Add location picker for reporting
- [ ] Add push notifications for critical alerts
- [ ] Add user authentication
- [ ] Add image uploads for hazard reports
- [ ] Add geofencing for location-based alerts



