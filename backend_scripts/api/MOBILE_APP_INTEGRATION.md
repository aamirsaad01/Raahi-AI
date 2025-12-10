# 📱 Mobile App Integration Guide

Complete guide for integrating the Raahi AI backend with your Flutter app.

---

## 🎯 User Flow Overview

### The Recommended Flow:

```
User Opens App
      ↓
User Sets: Budget + Mood + Activities
      ↓
API: GET RECOMMENDATIONS (5 destinations with photos)
      ↓
Display: Cards with destination photos & highlights
      ↓
User Selects: One destination card
      ↓
API: GENERATE FULL ITINERARY
      ↓
Display: Day-by-day detailed plan
```

---

## 🚀 Implementation Steps

### Step 1: User Input Screen

Create a form to collect:
- Budget (number input, PKR)
- Mood (multi-select chips)
  - Options: `adventurous`, `romantic`, `family`, `cultural`, `relaxed`
- Activities (multi-select chips, optional)
  - Options: `hiking`, `photography`, `camping`, `skiing`, `boating`, `sightseeing`
- Number of days (number input, default: 3)
- Travel month (dropdown, default: current month)

**Example UI:**
```dart
// Budget input
TextField(
  decoration: InputDecoration(labelText: 'Budget (PKR)'),
  keyboardType: TextInputType.number,
  onChanged: (value) => budget = double.parse(value),
)

// Mood selection
Wrap(
  children: [
    ChoiceChip(label: Text('Adventurous'), selected: selectedMoods.contains('adventurous')),
    ChoiceChip(label: Text('Romantic'), selected: selectedMoods.contains('romantic')),
    ChoiceChip(label: Text('Family'), selected: selectedMoods.contains('family')),
    // ... more chips
  ],
)
```

---

### Step 2: Call Recommendation API

When user clicks "Find Destinations" button:

```dart
Future<List<Destination>> getRecommendations({
  required double budget,
  required List<String> mood,
  List<String>? activities,
  int days = 3,
  int travelMonth = 5,
}) async {
  final url = Uri.parse('$baseUrl/api/itinerary/recommend');
  
  final response = await http.post(
    url,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'budget': budget,
      'mood': mood,
      'activities': activities ?? [],
      'days': days,
      'travel_month': travelMonth,
      'num_recommendations': 5,
    }),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    if (data['success']) {
      return (data['recommendations'] as List)
          .map((rec) => Destination.fromJson(rec))
          .toList();
    }
  }
  
  throw Exception('Failed to get recommendations');
}
```

**Response Structure:**
```dart
class Destination {
  final int rank;
  final String destination;
  final String region;
  final int locationId;
  final double matchScore;
  final DestinationPreview preview;
  
  Destination.fromJson(Map<String, dynamic> json)
      : rank = json['rank'],
        destination = json['destination'],
        region = json['region'],
        locationId = json['location_id'],
        matchScore = json['match_score'],
        preview = DestinationPreview.fromJson(json['preview']);
}

class DestinationPreview {
  final String title;
  final List<PreviewPhoto> photos;
  final List<String> highlights;
  final List<String> activities;
  final CostEstimate costEstimate;
  final int poiCount;
  final double? averageRating;
  
  // fromJson constructor...
}

class PreviewPhoto {
  final String poiName;
  final String photoUrl;
  final double? rating;
  
  PreviewPhoto.fromJson(Map<String, dynamic> json)
      : poiName = json['poi_name'],
        photoUrl = json['photo']['url'],
        rating = json['rating'];
}
```

---

### Step 3: Display Recommendation Cards

Show destinations as beautiful cards with photos:

```dart
ListView.builder(
  itemCount: recommendations.length,
  itemBuilder: (context, index) {
    final rec = recommendations[index];
    return DestinationCard(
      destination: rec,
      onTap: () => onDestinationSelected(rec),
    );
  },
)

// Destination Card Widget
class DestinationCard extends StatelessWidget {
  final Destination destination;
  final VoidCallback onTap;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(12),
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Photo Grid (4 photos)
            GridView.builder(
              shrinkWrap: true,
              physics: NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 1.5,
              ),
              itemCount: min(4, destination.preview.photos.length),
              itemBuilder: (context, i) {
                return Image.network(
                  destination.preview.photos[i].photoUrl,
                  fit: BoxFit.cover,
                );
              },
            ),
            
            Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title
                  Text(
                    '${destination.destination}, ${destination.region}',
                    style: Theme.of(context).textTheme.headline6,
                  ),
                  SizedBox(height: 8),
                  
                  // Match score
                  Row(
                    children: [
                      Icon(Icons.stars, color: Colors.amber),
                      SizedBox(width: 4),
                      Text('${destination.matchScore}% Match'),
                    ],
                  ),
                  SizedBox(height: 12),
                  
                  // Highlights
                  Text('Top Attractions:', 
                    style: TextStyle(fontWeight: FontWeight.bold)),
                  ...destination.preview.highlights.take(3).map(
                    (h) => Text('• $h'),
                  ),
                  SizedBox(height: 12),
                  
                  // Cost
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Estimated Cost:'),
                      Text(
                        'PKR ${destination.preview.costEstimate.estimatedCost.toStringAsFixed(0)}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: destination.preview.costEstimate.withinBudget 
                            ? Colors.green 
                            : Colors.orange,
                        ),
                      ),
                    ],
                  ),
                  
                  // POI count
                  Text('${destination.preview.poiCount} attractions included'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

### Step 4: User Selects Destination

When user taps a card:

```dart
void onDestinationSelected(Destination destination) {
  // Show loading
  showDialog(
    context: context,
    barrierDismissible: false,
    builder: (context) => Center(child: CircularProgressIndicator()),
  );
  
  // Generate full itinerary
  generateFullItinerary(
    userId: currentUserId,
    destination: destination.destination,
    budget: budget,
    mood: selectedMoods,
    activities: selectedActivities,
    days: days,
    travelMonth: travelMonth,
  ).then((itinerary) {
    Navigator.pop(context); // Close loading
    
    // Navigate to itinerary details page
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ItineraryDetailsPage(itinerary: itinerary),
      ),
    );
  }).catchError((error) {
    Navigator.pop(context);
    // Show error
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Failed to generate itinerary')),
    );
  });
}
```

---

### Step 5: Generate Full Itinerary

Call the generation API with selected destination:

```dart
Future<Itinerary> generateFullItinerary({
  required int userId,
  required String destination,
  required double budget,
  required List<String> mood,
  required List<String> activities,
  required int days,
  required int travelMonth,
}) async {
  final url = Uri.parse('$baseUrl/api/itinerary/generate');
  
  final response = await http.post(
    url,
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'user_id': userId,
      'destination': destination,
      'days': days,
      'budget': budget,
      'mood': mood,
      'activities': activities,
      'travel_month': travelMonth,
    }),
  );
  
  if (response.statusCode == 201) {
    final data = jsonDecode(response.body);
    if (data['success']) {
      return Itinerary.fromJson(data);
    }
  }
  
  throw Exception('Failed to generate itinerary');
}
```

---

### Step 6: Display Full Itinerary

Show day-by-day plan with POIs:

```dart
class ItineraryDetailsPage extends StatelessWidget {
  final Itinerary itinerary;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(itinerary.title)),
      body: ListView(
        children: [
          // Header
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(itinerary.title, 
                  style: Theme.of(context).textTheme.headline5),
                Text('${itinerary.destination}, ${itinerary.region}'),
                SizedBox(height: 16),
                
                // Cost breakdown
                Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      children: [
                        Text('Cost Breakdown', 
                          style: TextStyle(fontWeight: FontWeight.bold)),
                        Divider(),
                        _costRow('Attractions', 
                          itinerary.costBreakdown.breakdown.attractions),
                        _costRow('Accommodation', 
                          itinerary.costBreakdown.breakdown.accommodation),
                        _costRow('Food', 
                          itinerary.costBreakdown.breakdown.food),
                        _costRow('Transport', 
                          itinerary.costBreakdown.breakdown.transport),
                        Divider(),
                        _costRow('Total', 
                          itinerary.costBreakdown.totalEstimated,
                          bold: true),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Daily plans
          ...itinerary.dailyPlan.map((day) => DayCard(day: day)),
        ],
      ),
    );
  }
  
  Widget _costRow(String label, double amount, {bool bold = false}) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(
            fontWeight: bold ? FontWeight.bold : FontWeight.normal)),
          Text('PKR ${amount.toStringAsFixed(0)}', style: TextStyle(
            fontWeight: bold ? FontWeight.bold : FontWeight.normal)),
        ],
      ),
    );
  }
}

// Day Card Widget
class DayCard extends StatelessWidget {
  final DailyPlan day;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(12),
      child: ExpansionTile(
        title: Text('Day ${day.day} - ${day.date}'),
        subtitle: Text(
          '${day.activitiesCount} activities • ${day.totalDurationHours}h • PKR ${day.estimatedCost}'),
        children: day.pois.map((poi) => PoiListTile(poi: poi)).toList(),
      ),
    );
  }
}

// POI List Tile
class PoiListTile extends StatelessWidget {
  final Poi poi;
  
  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: CircleAvatar(
        child: Text(poi.time.substring(0, 5)),
      ),
      title: Text(poi.name),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(poi.description, maxLines: 2),
          SizedBox(height: 4),
          Row(
            children: [
              Icon(Icons.access_time, size: 16),
              Text(' ${poi.durationHours}h'),
              SizedBox(width: 12),
              Icon(Icons.attach_money, size: 16),
              Text(' PKR ${poi.cost}'),
              if (poi.rating != null) ...[
                SizedBox(width: 12),
                Icon(Icons.star, size: 16, color: Colors.amber),
                Text(' ${poi.rating}'),
              ],
            ],
          ),
        ],
      ),
      isThreeLine: true,
      onTap: () {
        // Show POI details dialog
        showPoiDetails(context, poi);
      },
    );
  }
}
```

---

## 📦 Complete Data Models

```dart
class Itinerary {
  final int itineraryId;
  final String title;
  final String destination;
  final String region;
  final int days;
  final double totalBudget;
  final CostBreakdown costBreakdown;
  final List<DailyPlan> dailyPlan;
  final LocationInfo locationInfo;
  final int selectedPoisCount;
  final int totalPoisAvailable;
  
  Itinerary.fromJson(Map<String, dynamic> json)
      : itineraryId = json['itinerary_id'],
        title = json['title'],
        destination = json['destination'],
        region = json['region'],
        days = json['days'],
        totalBudget = json['total_budget'],
        costBreakdown = CostBreakdown.fromJson(json['cost_breakdown']),
        dailyPlan = (json['daily_plan'] as List)
            .map((d) => DailyPlan.fromJson(d))
            .toList(),
        locationInfo = LocationInfo.fromJson(json['location_info']),
        selectedPoisCount = json['selected_pois_count'],
        totalPoisAvailable = json['total_pois_available'];
}

class DailyPlan {
  final int day;
  final String date;
  final List<Poi> pois;
  final double totalDurationHours;
  final double estimatedCost;
  final int activitiesCount;
  
  DailyPlan.fromJson(Map<String, dynamic> json)
      : day = json['day'],
        date = json['date'],
        pois = (json['pois'] as List).map((p) => Poi.fromJson(p)).toList(),
        totalDurationHours = json['total_duration_hours'],
        estimatedCost = json['estimated_cost'],
        activitiesCount = json['activities_count'];
}

class Poi {
  final int poiId;
  final String name;
  final String category;
  final String time;
  final double durationHours;
  final double cost;
  final double latitude;
  final double longitude;
  final String description;
  final double? rating;
  final String difficulty;
  final List<String> activities;
  final List<String> highlights;
  final List<Photo> photos;
  final double matchScore;
  
  Poi.fromJson(Map<String, dynamic> json)
      : poiId = json['poi_id'],
        name = json['name'],
        category = json['category'],
        time = json['time'],
        durationHours = json['duration_hours'],
        cost = json['cost'],
        latitude = json['latitude'],
        longitude = json['longitude'],
        description = json['description'],
        rating = json['rating'],
        difficulty = json['difficulty'],
        activities = List<String>.from(json['activities'] ?? []),
        highlights = List<String>.from(json['highlights'] ?? []),
        photos = (json['photos'] as List?)
            ?.map((p) => Photo.fromJson(p))
            .toList() ?? [],
        matchScore = json['match_score'];
}
```

---

## 🎨 UI/UX Tips

### Recommendation Cards:
- ✅ Use large, attractive photos (grid layout)
- ✅ Show match score prominently (percentage or stars)
- ✅ Display cost with color coding (green if within budget)
- ✅ Add "Tap to explore" hint
- ✅ Smooth animations on selection

### Loading States:
- ✅ Show skeleton loaders while fetching recommendations
- ✅ Display "Generating itinerary..." with progress indicator
- ✅ Add estimated time remaining (2-3 seconds)

### Error Handling:
- ✅ "No destinations found" → suggest broadening preferences
- ✅ "Budget too low" → suggest minimum budget
- ✅ Network errors → retry button

---

## 🔧 Configuration

**Base URL:**
```dart
// Development (same network)
const String baseUrl = 'http://192.168.1.10:5000';

// Production
const String baseUrl = 'https://your-api.herokuapp.com';
```

---

## ✅ Testing Checklist

- [ ] Test with different budgets (low, medium, high)
- [ ] Test with different moods
- [ ] Test with/without activities
- [ ] Test photo loading/caching
- [ ] Test offline handling
- [ ] Test error scenarios
- [ ] Test on different screen sizes

---

## 🎉 You're Ready!

This flow gives users:
- **Discovery** - Find new destinations they didn't know about
- **Visual** - See photos before deciding
- **Personalized** - AI matches their preferences
- **Simple** - No need to research destinations

**Happy coding! 🚀**

