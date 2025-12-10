# 🚀 Raahi AI Backend API Documentation

Complete REST API for itinerary generation and management.

---

## 📍 Base URL

```
http://localhost:5000
```

---

## 🔑 Authentication Endpoints

### 1. Register User

**POST** `/api/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "user_id": 1,
  "message": "User registered successfully"
}
```

**Error Response (400):**
```json
{
  "success": false,
  "error": "Email already exists"
}
```

---

### 2. Login User

**POST** `/api/auth/login`

Login with email and password.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "user_id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2025-12-10T10:00:00Z"
  },
  "message": "Login successful"
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": "Invalid email or password"
}
```

---

## 🗺️ Itinerary Endpoints

### 1. Recommend Destinations (NEW!)

**POST** `/api/itinerary/recommend`

Get personalized destination recommendations based on budget and mood (without specifying destination).

**Use Case:** User provides only budget and preferences, system recommends multiple destination options with photos. User then selects one to generate full itinerary.

**Request Body:**
```json
{
  "budget": 50000,
  "mood": ["adventurous", "romantic"],
  "activities": ["hiking", "photography"],
  "days": 3,
  "travel_month": 5,
  "num_recommendations": 5
}
```

**Field Descriptions:**
- `budget` (required): Total budget in PKR
- `mood` (required): Array of mood tags
  - Options: `"adventurous"`, `"romantic"`, `"family"`, `"cultural"`, `"relaxed"`
- `activities` (optional): Array of preferred activities
- `days` (optional): Number of days (default: 3)
- `travel_month` (optional): Month number 1-12 (default: 5)
- `num_recommendations` (optional): Number of destinations to recommend (default: 5)

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "recommendations": [
    {
      "rank": 1,
      "destination": "Hunza",
      "region": "Gilgit-Baltistan",
      "location_id": 45,
      "match_score": 87.5,
      "preview": {
        "title": "3-Day Hunza Adventure",
        "destination": "Hunza",
        "region": "Gilgit-Baltistan",
        "days": 3,
        "photos": [
          {
            "poi_name": "Attabad Lake",
            "photo": {
              "url": "https://images.unsplash.com/photo-123",
              "photographer": "John Smith"
            },
            "rating": 4.5
          },
          {
            "poi_name": "Rakaposhi Base Camp",
            "photo": {
              "url": "https://images.unsplash.com/photo-456",
              "photographer": "Jane Doe"
            },
            "rating": 4.8
          }
        ],
        "highlights": [
          "Attabad Lake",
          "Rakaposhi Base Camp",
          "Eagle's Nest Viewpoint"
        ],
        "activities": ["hiking", "photography", "boating", "camping"],
        "categories": ["nature", "adventure"],
        "cost_estimate": {
          "total_budget": 50000,
          "estimated_cost": 48500,
          "within_budget": true,
          "breakdown": {
            "attractions": 15000,
            "accommodation": 20000,
            "food": 10000,
            "transport": 3500
          }
        },
        "poi_count": 6,
        "average_rating": 4.3,
        "location_info": {
          "latitude": 36.3167,
          "longitude": 74.65,
          "elevation": 2438,
          "climate_zone": "alpine",
          "tourist_season": "March-October"
        }
      }
    },
    {
      "rank": 2,
      "destination": "Skardu",
      "region": "Gilgit-Baltistan",
      "match_score": 85.2,
      "preview": {...}
    }
  ],
  "search_criteria": {
    "budget": 50000,
    "mood": ["adventurous", "romantic"],
    "activities": ["hiking", "photography"],
    "days": 3,
    "travel_month": 5
  }
}
```

**Error Responses:**

**No Matching Destinations (400):**
```json
{
  "success": false,
  "error": "No destinations match your preferences",
  "suggestion": "Try increasing budget or broader mood preferences"
}
```

---

### 2. Generate Itinerary

**POST** `/api/itinerary/generate`

Generate a new personalized itinerary based on user preferences.

**Request Body:**
```json
{
  "user_id": 1,
  "destination": "Hunza",
  "days": 3,
  "budget": 50000,
  "mood": ["adventurous", "romantic"],
  "activities": ["hiking", "photography"],
  "travel_month": 5,
  "start_date": "2025-05-10"
}
```

**Field Descriptions:**
- `user_id` (required): User ID from login
- `destination` (required): City name (e.g., "Hunza", "Gilgit", "Skardu")
- `days` (required): Number of days (positive integer)
- `budget` (required): Total budget in PKR (positive number)
- `mood` (optional): Array of mood tags
  - Options: `"adventurous"`, `"romantic"`, `"family"`, `"cultural"`, `"relaxed"`
- `activities` (optional): Array of activities
  - Options: `"hiking"`, `"photography"`, `"camping"`, `"skiing"`, `"boating"`, `"sightseeing"`
- `travel_month` (optional): Month number (1-12), defaults to 5 (May)
- `start_date` (optional): Start date in "YYYY-MM-DD" format

**Response (201 Created):**
```json
{
  "success": true,
  "itinerary_id": 123,
  "title": "3-Day Adventure Hunza Trip",
  "destination": "Hunza",
  "region": "Gilgit-Baltistan",
  "days": 3,
  "total_budget": 50000,
  "cost_breakdown": {
    "total_budget": 50000,
    "total_estimated": 48500,
    "remaining": 1500,
    "breakdown": {
      "attractions": 15000,
      "accommodation": 20000,
      "food": 10000,
      "transport": 3500
    },
    "per_day": {
      "accommodation": 10000,
      "food": 3333.33
    }
  },
  "daily_plan": [
    {
      "day": 1,
      "date": "2025-05-10",
      "pois": [
        {
          "poi_id": 123,
          "name": "Attabad Lake",
          "category": "nature",
          "time": "09:00",
          "duration_hours": 3.5,
          "cost": 2000,
          "latitude": 36.3429,
          "longitude": 74.8667,
          "description": "Stunning turquoise lake formed after landslide...",
          "rating": 4.5,
          "difficulty": "easy",
          "activities": ["photography", "boating"],
          "highlights": ["Crystal clear water", "Boat rides", "Scenic views"],
          "photos": [
            {
              "url": "https://images.unsplash.com/photo-123",
              "photographer": "John Smith"
            }
          ],
          "match_score": 85.5
        }
      ],
      "total_duration_hours": 7.5,
      "estimated_cost": 12000,
      "activities_count": 2
    },
    {
      "day": 2,
      "date": "2025-05-11",
      "pois": [...],
      "total_duration_hours": 8.0,
      "estimated_cost": 18000,
      "activities_count": 2
    },
    {
      "day": 3,
      "date": "2025-05-12",
      "pois": [...],
      "total_duration_hours": 6.5,
      "estimated_cost": 18500,
      "activities_count": 2
    }
  ],
  "location_info": {
    "latitude": 36.3167,
    "longitude": 74.65,
    "elevation": 2438,
    "climate_zone": "alpine",
    "tourist_season": "March-October"
  },
  "selected_pois_count": 6,
  "total_pois_available": 15
}
```

**Error Responses:**

**Location Not Found (400):**
```json
{
  "success": false,
  "error": "Location 'XYZ' not found",
  "suggestion": "Please check the spelling or try a different location"
}
```

**No Attractions (400):**
```json
{
  "success": false,
  "error": "No attractions match your preferences",
  "suggestion": "Try broader mood/activity preferences"
}
```

**Budget Too Low (400):**
```json
{
  "success": false,
  "error": "Budget too low for any activities",
  "suggestion": "Increase budget or reduce number of days"
}
```

---

### 2. Get Itinerary by ID

**GET** `/api/itinerary/{itinerary_id}`

Retrieve a specific itinerary.

**Example:**
```
GET /api/itinerary/123
```

**Response (200 OK):**
```json
{
  "success": true,
  "itinerary": {
    "itinerary_id": 123,
    "user_id": 1,
    "title": "3-Day Adventure Hunza Trip",
    "destination": "Hunza",
    "days": 3,
    "budget": 50000,
    "season": "Spring",
    "daily_plan": [...],
    "total_cost": 48500,
    "mood_tags": ["adventurous", "romantic"],
    "activities": ["hiking", "photography"],
    "travel_month": 5,
    "created_at": "2025-12-10T10:00:00Z",
    "updated_at": "2025-12-10T10:00:00Z"
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": "Itinerary not found"
}
```

---

### 3. Get User Itineraries

**GET** `/api/itinerary/user/{user_id}`

Get all itineraries for a specific user.

**Example:**
```
GET /api/itinerary/user/1
```

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "itineraries": [
    {
      "itinerary_id": 123,
      "title": "3-Day Adventure Hunza Trip",
      "destination": "Hunza",
      "days": 3,
      "budget": 50000,
      "created_at": "2025-12-10T10:00:00Z"
    },
    {
      "itinerary_id": 122,
      "title": "5-Day Cultural Lahore Tour",
      "destination": "Lahore",
      "days": 5,
      "budget": 80000,
      "created_at": "2025-12-08T10:00:00Z"
    }
  ]
}
```

---

### 4. Update Itinerary

**PUT** `/api/itinerary/{itinerary_id}`

Update an existing itinerary.

**Request Body:**
```json
{
  "title": "Updated Title",
  "days": 4,
  "budget": 60000
}
```

**Allowed Fields:**
- `title`: New title
- `days`: Updated number of days
- `budget`: Updated budget
- `daily_plan`: Updated daily plan (full JSONB object)
- `total_cost`: Updated total cost

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Itinerary updated successfully"
}
```

---

### 5. Delete Itinerary

**DELETE** `/api/itinerary/{itinerary_id}`

Delete an itinerary.

**Example:**
```
DELETE /api/itinerary/123
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Itinerary deleted successfully"
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": "Itinerary not found"
}
```

---

## 🏥 Health Check

### Health Endpoint

**GET** `/api/health`

Check if API is running.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "message": "API is running"
}
```

---

## 🎯 Recommended User Flow

### Mobile App Flow (Recommended)

This is the recommended flow for your mobile app:

**Step 1: User provides preferences**
- Budget (e.g., 50,000 PKR)
- Mood tags (e.g., adventurous, romantic)
- Activities (optional)
- Number of days

**Step 2: Show recommendations**
```dart
// Call recommendation API
final response = await http.post(
  Uri.parse('$baseUrl/api/itinerary/recommend'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'budget': 50000,
    'mood': ['adventurous', 'romantic'],
    'activities': ['hiking', 'photography'],
    'days': 3,
    'travel_month': 5,
  }),
);

// Display recommendations as cards with:
// - Destination name
// - Preview photos (4 images)
// - Highlights (top 3 POIs)
// - Cost estimate
// - Match score
```

**Step 3: User selects destination**
```dart
// User taps on a recommendation card
// Get the selected destination's location_id or name
```

**Step 4: Generate full itinerary**
```dart
// Generate detailed itinerary for selected destination
final response = await http.post(
  Uri.parse('$baseUrl/api/itinerary/generate'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_id': userId,
    'destination': selectedDestination, // From step 3
    'days': 3,
    'budget': 50000,
    'mood': ['adventurous', 'romantic'],
    'activities': ['hiking', 'photography'],
    'travel_month': 5,
  }),
);

// Display full day-by-day itinerary
```

**Benefits of this flow:**
- ✅ User doesn't need to know destinations
- ✅ Visual selection with photos
- ✅ Multiple options to choose from
- ✅ AI-powered matching
- ✅ Budget-aware recommendations

---

## 📊 Example Use Cases

### Use Case 1: Recommendation-Based Flow (Recommended)

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ali Khan",
    "email": "ali@example.com",
    "password": "mypassword"
  }'

# Response: {"success": true, "user_id": 1}

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ali@example.com",
    "password": "mypassword"
  }'

# Response: {"success": true, "user": {...}}

# 3. Get Recommendations (without specifying destination)
curl -X POST http://localhost:5000/api/itinerary/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 50000,
    "mood": ["adventurous"],
    "activities": ["hiking", "photography"],
    "days": 3,
    "travel_month": 5
  }'

# Response: Multiple destination options with photos and previews

# 4. User selects "Hunza" from recommendations

# 5. Generate full itinerary for selected destination
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

# Response: Full day-by-day itinerary with POIs, timings, costs
```

### Use Case 2: Direct Generation (Alternative)

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ali Khan",
    "email": "ali@example.com",
    "password": "mypassword"
  }'

# Response: {"success": true, "user_id": 1}

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ali@example.com",
    "password": "mypassword"
  }'

# Response: {"success": true, "user": {...}}

# 3. Generate Itinerary
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

# Response: {"success": true, "itinerary_id": 123, "daily_plan": [...]}

# 4. Get User's Itineraries
curl http://localhost:5000/api/itinerary/user/1

# 5. Get Specific Itinerary
curl http://localhost:5000/api/itinerary/123

# 6. Update Itinerary
curl -X PUT http://localhost:5000/api/itinerary/123 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Hunza Adventure"
  }'

# 7. Delete Itinerary
curl -X DELETE http://localhost:5000/api/itinerary/123
```

---

## 🌍 Available Destinations

The API supports 138 locations across Pakistan, including:

**Popular Destinations:**
- Hunza, Skardu, Gilgit, Naran, Kaghan, Murree, Swat, Chitral, Dir, Fairy Meadows, Ratti Gali, Astore Valley, and many more...

**To see all available locations:**
```sql
SELECT city, parent_region FROM location_mapping WHERE verified = TRUE ORDER BY city;
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in project root:

```env
# Database
DB_NAME=raahi_ai
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

# API
PORT=5000
```

---

## 🚦 HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid credentials |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Server error |

---

## 🎯 POI Matching Algorithm

The system uses a sophisticated matching algorithm that:

1. **Filters POIs** by:
   - Location (destination city)
   - Mood tags (adventurous, romantic, etc.)
   - Activities (hiking, photography, etc.)
   - Travel season (best months to visit)

2. **Scores POIs** based on:
   - Rating (30 points)
   - Mood match (25 points)
   - Activity match (25 points)
   - Budget fit (10 points)
   - Season match (10 points)

3. **Selects POIs** that:
   - Fit within budget (30% allocated to attractions)
   - Provide 2-4 activities per day
   - Match user preferences (>30% match score)

4. **Schedules POIs**:
   - Distributes across days (6-8 hours per day)
   - Assigns time slots starting at 9 AM
   - Includes buffer time for travel

---

## 📦 Budget Allocation

Default budget breakdown:
- **Attractions**: 30%
- **Accommodation**: 40%
- **Food**: 20%
- **Transport**: 10%

Example for 50,000 PKR budget:
- Attractions: 15,000 PKR
- Hotels: 20,000 PKR
- Food: 10,000 PKR
- Transport: 5,000 PKR

---

## 🔧 Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Description of error",
  "suggestion": "Helpful suggestion (optional)"
}
```

---

## 📱 Mobile App Integration

For Flutter/React Native apps:

```dart
// Example: Generate Itinerary
final response = await http.post(
  Uri.parse('http://your-server:5000/api/itinerary/generate'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_id': userId,
    'destination': 'Hunza',
    'days': 3,
    'budget': 50000,
    'mood': ['adventurous'],
    'activities': ['hiking'],
    'travel_month': 5,
  }),
);

if (response.statusCode == 201) {
  final data = jsonDecode(response.body);
  print('Itinerary ID: ${data['itinerary_id']}');
}
```

---

## 🎉 Ready to Use!

The API is fully functional and ready for integration with your mobile app!

For questions or issues, refer to the code documentation or check server logs.

