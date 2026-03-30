# Itinerary Feature - Backend Integration Summary

## ✅ What Was Done

The itinerary feature has been fully integrated with the backend API. The frontend now communicates with the unified backend server to generate real itineraries.

## 📁 Files Created/Modified

### New Files:
1. **`api_service.dart`** - API service for communicating with the backend
   - Handles all itinerary-related API calls
   - Maps backend responses to frontend models
   - Includes error handling

### Modified Files:
1. **`models.dart`** - Added `destination` field to `ItineraryFormData`
2. **`itinerary_page.dart`** - Added destination input field with popular destinations dropdown
3. **`results_page.dart`** - Completely refactored to:
   - Call backend API instead of using fake data
   - Show loading state while generating itinerary
   - Display error messages if API call fails
   - Show generated itinerary with real data

## 🔌 API Integration

### Endpoints Used:
- `POST /api/itinerary/generate` - Generate new itinerary
- `POST /api/itinerary/recommend` - Get destination recommendations (available but not yet used in UI)
- `GET /api/itinerary/<id>` - Get itinerary by ID (available but not yet used in UI)
- `GET /api/itinerary/user/<user_id>` - Get user's itineraries (available but not yet used in UI)

### Request Format:
```json
{
  "user_id": 1,
  "destination": "Hunza",
  "days": 6,
  "budget": 120000,
  "mood": ["adventurous"],
  "activities": ["Hiking", "Photography"],
  "travel_month": 7
}
```

### Response Format:
The backend returns a complete itinerary with:
- `itinerary_id` - Unique ID
- `title` - Generated title
- `destination` - Destination name
- `region` - Region name
- `daily_plan` - Array of day plans with POIs
- `cost_breakdown` - Cost breakdown by category
- `highlights` - Array of highlights

## 🎨 UI Changes

1. **Form Page** (`itinerary_page.dart`):
   - Added destination text field with dropdown for popular destinations
   - Default destination: "Hunza"
   - Popular destinations include: Hunza, Naran, Skardu, Swat, Murree, etc.

2. **Results Page** (`results_page.dart`):
   - Loading spinner while generating itinerary
   - Error screen with retry button if generation fails
   - Budget card showing estimated cost
   - Highlights chips
   - Daily plan cards with POI names

## ⚙️ Configuration

### Backend URL:
The API service uses `http://127.0.0.1:5000` by default. To change it:

1. **For iOS Simulator**: Use `http://localhost:5000` or `http://127.0.0.1:5000`
2. **For Android Emulator**: Use `http://10.0.2.2:5000`
3. **For Physical Device**: Use your computer's IP address (e.g., `http://192.168.1.100:5000`)

Edit `mobile_app/lib/features/itinerary/api_service.dart`:
```dart
static const String baseUrl = 'http://YOUR_IP:5000';
```

## 🚀 How to Use

1. **Start the Backend Server**:
   ```bash
   cd backend_scripts/api
   python app.py
   ```

2. **Run the Flutter App**:
   ```bash
   cd mobile_app
   flutter run
   ```

3. **Generate Itinerary**:
   - Fill in the form (mood, destination, budget, season, activities, duration)
   - Click "Generate Itinerary"
   - Wait for the API to generate your itinerary
   - View the results with real POIs and daily plans

## 🔧 TODO / Future Enhancements

1. **User Authentication**: Currently uses `userId: 1`. Should integrate with auth system.
2. **Destination Recommendations**: The `/recommend` endpoint is available but not yet used in UI. Could add a "Get Recommendations" button.
3. **Save Itineraries**: Could add functionality to save and retrieve user's itineraries.
4. **Error Handling**: Could add more specific error messages for different failure scenarios.
5. **Offline Support**: Could cache generated itineraries for offline viewing.

## 📝 Notes

- The backend must be running for the feature to work
- Ensure the backend URL matches your setup (see Configuration section)
- The API service handles all JSON parsing and error handling
- All backend responses are mapped to frontend models automatically

