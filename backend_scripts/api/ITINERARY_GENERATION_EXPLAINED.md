# 🗺️ Itinerary Generation Backend - Complete Explanation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Request Flow](#request-flow)
4. [Step-by-Step Process](#step-by-step-process)
5. [Key Components](#key-components)
6. [Algorithms & Logic](#algorithms--logic)
7. [Database Schema](#database-schema)

---

## 🎯 Overview

The itinerary generation system creates personalized day-by-day travel itineraries based on:
- **Destination** (e.g., "Hunza", "Naran", "Skardu")
- **Budget** (total PKR)
- **Duration** (number of days)
- **Mood** (adventurous, romantic, family, cultural, relaxed)
- **Activities** (hiking, photography, camping, etc.)
- **Travel Month** (1-12)

The system intelligently matches Points of Interest (POIs) to user preferences, ranks them, selects within budget, and creates a day-by-day schedule.

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Flask API      │  (api/routes/itinerary.py)
│  /api/itinerary │
│  /generate      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Itinerary       │  (api/services/itinerary_generator.py)
│ Generator       │  - Main orchestration logic
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│Database│ │ POI      │  (api/services/poi_matcher.py)
│Helper  │ │ Matcher  │  - Scoring & ranking algorithm
└────────┘ └──────────┘
    │
    ▼
┌──────────────┐
│ PostgreSQL   │
│ Database     │
│ - locations  │
│ - pois       │
│ - itineraries│
└──────────────┘
```

---

## 🔄 Request Flow

### 1. **API Endpoint** (`POST /api/itinerary/generate`)

**Location:** `backend_scripts/api/routes/itinerary.py`

**Request Example:**
```json
{
  "destination": "Hunza",
  "days": 6,
  "budget": 120000,
  "mood": ["adventurous"],
  "activities": ["hiking", "photography"],
  "travel_month": 7
}
```

**What it does:**
- Validates required fields (destination, days, budget)
- Makes `user_id` optional (defaults to `None` for anonymous users)
- Sets default values for optional fields
- Calls `ItineraryGenerator.generate()`
- Returns JSON response

---

## 📝 Step-by-Step Process

### **Step 1: Validate Location** 
**File:** `itinerary_generator.py` line 47

```python
location = self.db.get_location_by_city(user_prefs['destination'])
```

- Queries `location_mapping` table
- Checks if destination exists and is verified
- Returns location details (coordinates, region, climate, etc.)
- **Error if:** Location not found → Returns error with suggestion

---

### **Step 2: Fetch POIs for Location**
**File:** `itinerary_generator.py` line 56

```python
pois = self.db.get_pois_for_location(
    location_id=location['location_id'],
    mood_tags=user_prefs.get('mood'),
    activities=user_prefs.get('activities')
)
```

**Database Query:**
- Fetches all POIs from `points_of_interest` table
- Filters by `location_id`
- Optionally filters by mood tags (JSONB array contains)
- Optionally filters by activities (JSONB array contains)
- Orders by rating (DESC) and cost (ASC)

**Error if:** No POIs found → Returns error with suggestion

---

### **Step 3: Filter & Rank POIs**
**File:** `itinerary_generator.py` line 70

```python
ranked_pois = self.matcher.filter_and_rank_pois(pois, user_prefs)
```

**Algorithm:** `POIMatcher.calculate_match_score()`

**Scoring System (0-100 points):**

1. **Rating Score (30 points max)**
   - Formula: `(rating / 5.0) * 30`
   - Higher rated POIs get more points

2. **Mood Match (25 points max)**
   - Checks overlap between user moods and POI mood_tags
   - Formula: `(mood_overlap / total_user_moods) * 25`
   - Example: User has ["adventurous", "romantic"], POI has ["adventurous"] → 12.5 points

3. **Activity Match (25 points max)**
   - Checks overlap between user activities and POI activities
   - Formula: `(activity_overlap / total_user_activities) * 25`
   - Example: User has ["hiking", "photography"], POI has both → 25 points

4. **Budget Match (10 points max)**
   - Calculates daily budget: `total_budget / days`
   - POI budget limit: `daily_budget * 0.4` (40% of daily budget for activities)
   - If POI cost ≤ limit: 10 points
   - If POI cost ≤ limit * 1.5: 5 points
   - Otherwise: 0 points

5. **Season Match (10 points max)**
   - Checks if travel month matches POI's best_months
   - If good time to visit: 10 points

**Filtering:**
- Only includes POIs with score ≥ 30 (30% match minimum)
- Sorts by match score (descending)

**Error if:** No POIs match preferences → Returns error with suggestion

---

### **Step 4: Select POIs Within Budget**
**File:** `itinerary_generator.py` line 80

```python
selected_pois = self.matcher.select_pois_within_budget(
    ranked_pois,
    user_prefs['budget'],
    user_prefs['days']
)
```

**Budget Allocation:**
- **30%** for attractions/POIs
- **40%** for accommodation
- **20%** for food
- **10%** for transport

**Selection Algorithm:**
1. Calculate POI budget: `total_budget * 0.30`
2. Iterate through ranked POIs (highest score first)
3. Add POI if: `current_cost + poi_cost ≤ poi_budget`
4. Stop when: `selected_count ≥ days * 3` (aim for 2-4 POIs per day)

**Error if:** Budget too low → Returns error with suggestion

---

### **Step 5: Create Day-by-Day Schedule**
**File:** `itinerary_generator.py` line 94, method `_create_daily_schedule()`

**Algorithm:**
1. **Distribute POIs across days**
   - Target: 6-8 hours of activities per day
   - Start time: 9:00 AM
   - Calculate duration for each POI: `avg_duration_hours + 1 hour buffer`

2. **For each day:**
   - Add POIs until day duration reaches ~7 hours
   - Calculate start time for each POI
   - Track total cost per day
   - Generate date (if start_date provided, else use current date)

3. **Daily Plan Structure:**
```json
{
  "day": 1,
  "date": "2025-07-15",
  "pois": [
    {
      "poi_id": 45,
      "name": "Attabad Lake",
      "category": "Natural",
      "time": "09:00",
      "duration_hours": 3.0,
      "cost": 5000,
      "latitude": 36.3167,
      "longitude": 74.6500,
      "description": "...",
      "rating": 4.5,
      "difficulty": "Easy",
      "activities": ["boating", "photography"],
      "highlights": ["Crystal clear water", "Mountain views"],
      "photos": [...],
      "match_score": 87.5
    }
  ],
  "total_duration_hours": 7.5,
  "estimated_cost": 5000,
  "activities_count": 2
}
```

---

### **Step 6: Calculate Costs**
**File:** `itinerary_generator.py` line 101, method `_calculate_costs()`

**Cost Breakdown:**

1. **Attractions/POIs:**
   - Sum of all selected POI costs

2. **Accommodation:**
   - Per night: `(total_budget * 0.40) / (days - 1)`
   - Total: `per_night * (days - 1)`

3. **Food:**
   - Per day: `(total_budget * 0.20) / days`
   - Total: `per_day * days`

4. **Transport:**
   - Fixed: `total_budget * 0.10`

**Response:**
```json
{
  "total_budget": 120000,
  "total_estimated": 115000,
  "remaining": 5000,
  "breakdown": {
    "attractions": 36000,
    "accommodation": 48000,
    "food": 24000,
    "transport": 12000
  },
  "per_day": {
    "accommodation": 9600,
    "food": 4000
  }
}
```

---

### **Step 7: Generate Title**
**File:** `itinerary_generator.py` line 108, method `_generate_title()`

**Format:** `"{days}-Day {mood} {destination} Trip"`

**Examples:**
- "6-Day Adventure Hunza Trip"
- "3-Day Romantic Naran Trip"
- "5-Day Family Skardu Trip"

---

### **Step 8: Save to Database**
**File:** `itinerary_generator.py` line 134

```python
itinerary_id = self.db.save_itinerary(itinerary_data)
```

**Database Table:** `itineraries`

**Fields Saved:**
- `user_id` (NULL for anonymous users)
- `title`
- `destination`
- `days`
- `budget`
- `season` (calculated from travel_month)
- `daily_plan` (JSON)
- `total_cost`
- `mood_tags` (JSON array)
- `activities` (JSON array)
- `travel_month`

---

### **Step 9: Return Complete Itinerary**
**File:** `itinerary_generator.py` line 137

**Response Structure:**
```json
{
  "success": true,
  "itinerary_id": 123,
  "title": "6-Day Adventure Hunza Trip",
  "destination": "Hunza",
  "region": "Gilgit-Baltistan",
  "days": 6,
  "total_budget": 120000,
  "cost_breakdown": {...},
  "daily_plan": [...],
  "location_info": {
    "latitude": 36.3167,
    "longitude": 74.6500,
    "elevation": 2500,
    "climate_zone": "Highland",
    "tourist_season": "Summer"
  },
  "selected_pois_count": 12,
  "total_pois_available": 45
}
```

---

## 🔧 Key Components

### **1. ItineraryGenerator** (`api/services/itinerary_generator.py`)

**Responsibilities:**
- Orchestrates the entire generation process
- Calls database helper and POI matcher
- Creates daily schedules
- Calculates costs
- Saves to database

**Key Methods:**
- `generate(user_prefs)` - Main generation method
- `_create_daily_schedule()` - Distributes POIs across days
- `_calculate_costs()` - Budget breakdown
- `_generate_title()` - Creates itinerary title

---

### **2. POIMatcher** (`api/services/poi_matcher.py`)

**Responsibilities:**
- Scores POIs based on user preferences
- Ranks POIs by match score
- Selects POIs within budget
- Estimates time needed for POIs

**Key Methods:**
- `calculate_match_score(poi, user_prefs)` - Scoring algorithm
- `filter_and_rank_pois(pois, user_prefs)` - Filter & sort
- `select_pois_within_budget(pois, budget, days)` - Budget selection
- `estimate_time_for_poi(poi)` - Time estimation
- `is_good_time_to_visit(poi, month)` - Season matching

---

### **3. DatabaseHelper** (`api/utils/db_helper.py`)

**Responsibilities:**
- Database connection management
- Query execution
- Data type conversion (Decimal → float)
- CRUD operations for itineraries

**Key Methods:**
- `get_location_by_city(city)` - Find location
- `get_pois_for_location(location_id, ...)` - Fetch POIs with filters
- `save_itinerary(itinerary_data)` - Save itinerary
- `get_itinerary(itinerary_id)` - Retrieve itinerary
- `get_user_itineraries(user_id)` - Get user's itineraries

---

## 🧮 Algorithms & Logic

### **Match Scoring Formula**

```
Total Score = Rating Score + Mood Score + Activity Score + Budget Score + Season Score

Where:
- Rating Score = (rating / 5.0) * 30
- Mood Score = (mood_overlap / total_user_moods) * 25
- Activity Score = (activity_overlap / total_user_activities) * 25
- Budget Score = 10 if cost ≤ limit, else 5 if cost ≤ 1.5*limit, else 0
- Season Score = 10 if good time, else 0
```

### **Budget Allocation**

```
Total Budget = 100%

Breakdown:
- Attractions/POIs: 30%
- Accommodation: 40%
- Food: 20%
- Transport: 10%
```

### **Daily Schedule Algorithm**

```
For each day:
  target_hours = 7
  current_duration = 0
  
  While current_duration < target_hours:
    poi_duration = avg_duration_hours + 1 hour buffer
    if current_duration + poi_duration ≤ target_hours + 2:
      Add POI to day
      current_duration += poi_duration
      start_time = 9:00 + current_duration
    else:
      Move to next day
```

---

## 🗄️ Database Schema

### **Tables Used:**

1. **`location_mapping`**
   - Stores destination locations
   - Fields: `location_id`, `city`, `parent_region`, `latitude`, `longitude`, `elevation`, `climate_zone`, `tourist_season`

2. **`points_of_interest`**
   - Stores POIs/attractions
   - Fields: `poi_id`, `location_id`, `name`, `category`, `rating`, `mood_tags` (JSONB), `activities` (JSONB), `estimated_cost_pkr_max`, `avg_duration_hours`, `difficulty`, `best_months`, `description`, `highlights`, `photos`

3. **`itineraries`**
   - Stores generated itineraries
   - Fields: `itinerary_id`, `user_id` (nullable), `title`, `destination`, `days`, `budget`, `season`, `daily_plan` (JSON), `total_cost`, `mood_tags` (JSON), `activities` (JSON), `travel_month`, `created_at`, `updated_at`

---

## 🎯 Example Flow

**Input:**
```json
{
  "destination": "Hunza",
  "days": 6,
  "budget": 120000,
  "mood": ["adventurous"],
  "activities": ["hiking", "photography"],
  "travel_month": 7
}
```

**Process:**
1. ✅ Find "Hunza" in location_mapping → Found (location_id: 45)
2. ✅ Fetch 45 POIs for Hunza matching adventurous mood
3. ✅ Score and rank POIs → Top 12 selected
4. ✅ Select 12 POIs within 36,000 PKR budget (30% of 120,000)
5. ✅ Distribute 12 POIs across 6 days (2 POIs per day, ~7 hours/day)
6. ✅ Calculate costs: 115,000 PKR total
7. ✅ Generate title: "6-Day Adventure Hunza Trip"
8. ✅ Save to database → itinerary_id: 123
9. ✅ Return complete itinerary

**Output:**
- 6-day schedule with 2 POIs per day
- Cost breakdown showing all expenses
- Daily plans with times, locations, descriptions
- Total estimated cost: 115,000 PKR (within budget)

---

## 🔍 Error Handling

The system provides helpful error messages:

- **Location not found:** "Location 'X' not found. Please check spelling or try different location."
- **No POIs found:** "No attractions found. Try different mood/activity preferences."
- **No matches:** "No attractions match preferences. Try broader preferences."
- **Budget too low:** "Budget too low. Increase budget or reduce days."

---

## 🚀 Performance Considerations

- **Database Indexing:** Queries use indexes on `location_id`, `rating`, `cost`
- **Filtering:** Mood/activity filters use JSONB containment operators (`@>`)
- **Scoring:** Calculated in-memory for fast ranking
- **Budget Selection:** Greedy algorithm (O(n)) for fast selection

---

## 📚 Additional Features

### **Destination Recommendations** (`/api/itinerary/recommend`)
- Recommends multiple destinations based on budget/mood
- Shows preview with photos and highlights
- User selects one to generate full itinerary

### **Itinerary Management**
- `GET /api/itinerary/<id>` - Get itinerary by ID
- `GET /api/itinerary/user/<user_id>` - Get user's itineraries
- `PUT /api/itinerary/<id>` - Update itinerary
- `DELETE /api/itinerary/<id>` - Delete itinerary

---

This system creates personalized, budget-aware, day-by-day travel itineraries by intelligently matching user preferences with available attractions!

