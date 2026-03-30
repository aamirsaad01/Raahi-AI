import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models.dart';

class ItineraryApiService {
  // Change this to your backend URL
  // For local testing: 'http://localhost:5000' or 'http://127.0.0.1:5000'
  // For Android emulator: 'http://10.0.2.2:5000'
  static const String baseUrl = 'http://127.0.0.1:5000';

  /// Get destination recommendations based on budget and mood
  Future<Map<String, dynamic>> recommendDestinations({
    required int budget,
    required List<String> mood,
    List<String>? activities,
    int days = 3,
    int travelMonth = 5,
    int numRecommendations = 5,
    int numPeople = 1,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/itinerary/recommend'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'budget': budget,
          'mood': mood,
          'activities': activities ?? [],
          'days': days,
          'travel_month': travelMonth,
          'num_recommendations': numRecommendations,
          'num_people': numPeople,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return data;
        } else {
          throw Exception(data['error'] ?? 'Failed to get recommendations');
        }
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to get recommendations');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Generate full itinerary
  Future<TripItinerary> generateItinerary({
    int? userId,
    required String destination,
    required int days,
    required int budget,
    List<String>? mood,
    List<String>? activities,
    int? travelMonth,
    String? startDate,
    int numPeople = 1,
  }) async {
    try {
      final Map<String, dynamic> requestBody = {
        'destination': destination,
        'days': days,
        'budget': budget,
        'mood': mood ?? [],
        'activities': activities ?? [],
        'num_people': numPeople,
        if (travelMonth != null) 'travel_month': travelMonth,
        if (startDate != null) 'start_date': startDate,
      };
      
      // Only include user_id if provided
      if (userId != null && userId > 0) {
        requestBody['user_id'] = userId;
      }
      
      final response = await http.post(
        Uri.parse('$baseUrl/api/itinerary/generate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(requestBody),
      );

      if (response.statusCode == 201 || response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return _parseItineraryResponse(data);
        } else {
          throw Exception(data['error'] ?? 'Failed to generate itinerary');
        }
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to generate itinerary');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Get itinerary by ID
  Future<TripItinerary> getItinerary(int itineraryId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/itinerary/$itineraryId'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          return _parseItineraryResponse(data['itinerary']);
        } else {
          throw Exception(data['error'] ?? 'Failed to get itinerary');
        }
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to get itinerary');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Get user's itineraries
  Future<List<TripItinerary>> getUserItineraries(int userId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/itinerary/user/$userId'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> itinerariesJson = data['itineraries'] ?? [];
          return itinerariesJson.map((json) => _parseItineraryResponse(json)).toList();
        } else {
          throw Exception(data['error'] ?? 'Failed to get itineraries');
        }
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to get itineraries');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Parse backend response to TripItinerary model
  TripItinerary _parseItineraryResponse(Map<String, dynamic> data) {
    // Parse daily plan
    final List<DayPlan> days = [];
    final dailyPlan = data['daily_plan'] as List<dynamic>? ?? [];
    
    for (var dayData in dailyPlan) {
      final List<Poi> pois = [];
      final poisData = dayData['pois'] as List<dynamic>? ?? [];
      
      for (var poiData in poisData) {
        // Extract photo URLs
        final List<String> photos = [];
        final photosData = poiData['photos'] as List<dynamic>? ?? [];
        for (var photo in photosData) {
          if (photo is Map && photo['url'] != null) {
            photos.add(photo['url'] as String);
          } else if (photo is String) {
            photos.add(photo);
          }
        }
        
        // Safely convert numeric values
        final costValue = poiData['cost'];
        final double? cost = costValue is int 
            ? costValue.toDouble() 
            : costValue is double 
                ? costValue 
                : (costValue is num ? costValue.toDouble() : null);
        
        final durationValue = poiData['duration_hours'];
        final double? duration = durationValue is int 
            ? durationValue.toDouble() 
            : durationValue is double 
                ? durationValue 
                : (durationValue is num ? durationValue.toDouble() : null);
        
        final latValue = poiData['latitude'];
        final double? lat = latValue is int 
            ? latValue.toDouble() 
            : latValue is double 
                ? latValue 
                : (latValue is num ? latValue.toDouble() : null);
        
        final lonValue = poiData['longitude'];
        final double? lon = lonValue is int 
            ? lonValue.toDouble() 
            : lonValue is double 
                ? lonValue 
                : (lonValue is num ? lonValue.toDouble() : null);
        
        final ratingValue = poiData['rating'];
        final double? rating = ratingValue is int 
            ? ratingValue.toDouble() 
            : ratingValue is double 
                ? ratingValue 
                : (ratingValue is num ? ratingValue.toDouble() : null);
        
        final matchScoreValue = poiData['match_score'];
        final double? matchScore = matchScoreValue is int 
            ? matchScoreValue.toDouble() 
            : matchScoreValue is double 
                ? matchScoreValue 
                : (matchScoreValue is num ? matchScoreValue.toDouble() : null);
        
        pois.add(Poi(
          id: poiData['poi_id']?.toString() ?? '',
          name: poiData['name'] ?? 'Unknown',
          region: data['region'] ?? 'Unknown',
          description: poiData['description'],
          photos: photos,
          bestSeason: _getSeasonFromMonth(data['travel_month'] ?? 5),
          activityType: poiData['category'] ?? 'General',
          difficulty: poiData['difficulty'] ?? 'Easy',
          time: poiData['time'],
          durationHours: duration,
          cost: cost,
          latitude: lat,
          longitude: lon,
          rating: rating,
          activities: (poiData['activities'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
          highlights: (poiData['highlights'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
          matchScore: matchScore,
        ));
      }
      
      // Safely convert day number to int
      final dayValue = dayData['day'] ?? 1;
      final int dayNumber = dayValue is int 
          ? dayValue 
          : dayValue is double 
              ? dayValue.toInt() 
              : (dayValue is num ? dayValue.toInt() : 1);
      
      final durationValue = dayData['total_duration_hours'];
      final double? totalDuration = durationValue is int 
          ? durationValue.toDouble() 
          : durationValue is double 
              ? durationValue 
              : (durationValue is num ? durationValue.toDouble() : null);
      
      final costValue = dayData['estimated_cost'];
      final double? dayCost = costValue is int 
          ? costValue.toDouble() 
          : costValue is double 
              ? costValue 
              : (costValue is num ? costValue.toDouble() : null);
      
      final activitiesCount = dayData['activities_count'] as int?;
      
      days.add(DayPlan(
        dayNumber: dayNumber,
        date: dayData['date'],
        stops: pois,
        notes: dayData['summary'] ?? dayData['notes'],
        totalDurationHours: totalDuration,
        estimatedCost: dayCost,
        activitiesCount: activitiesCount,
      ));
    }

    // Parse cost breakdown
    final costBreakdownData = data['cost_breakdown'] as Map<String, dynamic>?;
    CostBreakdown? costBreakdown;
    if (costBreakdownData != null) {
      final breakdownData = costBreakdownData['breakdown'] as Map<String, dynamic>? ?? {};
      final perDayData = costBreakdownData['per_day'] as Map<String, dynamic>?;
      
      costBreakdown = CostBreakdown(
        totalBudget: _toDouble(costBreakdownData['total_budget'] ?? 0),
        totalEstimated: _toDouble(costBreakdownData['total_estimated'] ?? 0),
        remaining: _toDouble(costBreakdownData['remaining'] ?? 0),
        breakdown: CostBreakdownDetails(
          attractions: _toDouble(breakdownData['attractions'] ?? 0),
          accommodation: _toDouble(breakdownData['accommodation'] ?? 0),
          food: _toDouble(breakdownData['food'] ?? 0),
          transport: _toDouble(breakdownData['transport'] ?? 0),
        ),
        perDay: perDayData != null ? CostPerDay(
          accommodation: _toDouble(perDayData['accommodation'] ?? 0),
          food: _toDouble(perDayData['food'] ?? 0),
        ) : null,
      );
    }
    
    // Parse location info
    final locationInfoData = data['location_info'] as Map<String, dynamic>?;
    LocationInfo? locationInfo;
    if (locationInfoData != null) {
      locationInfo = LocationInfo(
        latitude: _toDouble(locationInfoData['latitude'] ?? 0),
        longitude: _toDouble(locationInfoData['longitude'] ?? 0),
        elevation: locationInfoData['elevation'] != null ? _toDouble(locationInfoData['elevation']) : null,
        climateZone: locationInfoData['climate_zone'],
        touristSeason: locationInfoData['tourist_season'],
      );
    }
    
    // Extract highlights from POIs
    final List<String> highlights = [];
    for (var day in dailyPlan) {
      final poisData = day['pois'] as List<dynamic>? ?? [];
      for (var poi in poisData) {
        final poiHighlights = poi['highlights'] as List<dynamic>? ?? [];
        highlights.addAll(poiHighlights.map((h) => h.toString()));
      }
    }
    // Remove duplicates and limit
    highlights.removeWhere((h) => h.isEmpty);
    final uniqueHighlights = highlights.toSet().toList();
    final finalHighlights = uniqueHighlights.length > 5 
        ? uniqueHighlights.sublist(0, 5) 
        : uniqueHighlights;

    // Safely convert cost to int (backend may return double)
    final costValue = costBreakdownData?['total_estimated'] ?? data['total_budget'] ?? 0;
    final int estimatedCost = costValue is int 
        ? costValue 
        : costValue is double 
            ? costValue.toInt() 
            : (costValue is num ? costValue.toInt() : 0);
    
    // Safely convert days to int
    final daysValue = data['days'];
    final int daysCount = daysValue is int 
        ? daysValue 
        : daysValue is double 
            ? daysValue.toInt() 
            : (daysValue is num ? daysValue.toInt() : days.length);
    
    // Safely convert total budget to int
    final budgetValue = data['total_budget'] ?? data['budget'] ?? 0;
    final int totalBudget = budgetValue is int 
        ? budgetValue 
        : budgetValue is double 
            ? budgetValue.toInt() 
            : (budgetValue is num ? budgetValue.toInt() : 0);
    
    return TripItinerary(
      id: data['itinerary_id']?.toString() ?? data['id']?.toString() ?? '0',
      title: data['title'] ?? 'Untitled Itinerary',
      destination: data['destination'] ?? 'Unknown',
      region: data['region'] ?? 'Unknown',
      days: daysCount,
      totalBudget: totalBudget,
      daysPlan: days,
      estimatedCost: estimatedCost,
      highlights: finalHighlights.isEmpty 
          ? ['Scenic Views', 'Local Cuisine', 'Comfortable Stays'] 
          : finalHighlights,
      costBreakdown: costBreakdown,
      locationInfo: locationInfo,
      selectedPoisCount: data['selected_pois_count'] as int? ?? 0,
      totalPoisAvailable: data['total_pois_available'] as int? ?? 0,
    );
  }
  
  double _toDouble(dynamic value) {
    if (value is int) return value.toDouble();
    if (value is double) return value;
    if (value is num) return value.toDouble();
    return 0.0;
  }

  String _getSeasonFromMonth(int month) {
    if (month >= 3 && month <= 5) return 'Spring';
    if (month >= 6 && month <= 8) return 'Summer';
    if (month >= 9 && month <= 11) return 'Autumn';
    return 'Winter';
  }

  /// Convert mood enum to backend format
  List<String> moodToBackend(Mood mood) {
    switch (mood) {
      case Mood.adventurous:
        return ['adventurous'];
      case Mood.relaxed:
        return ['relaxed'];
      case Mood.romantic:
        return ['romantic'];
      case Mood.family:
        return ['family'];
      case Mood.cultural:
        return ['cultural'];
    }
  }

  /// Convert season string to month number
  int seasonToMonth(String season) {
    switch (season.toLowerCase()) {
      case 'spring':
        return 4; // April
      case 'summer':
        return 7; // July
      case 'autumn':
      case 'fall':
        return 10; // October
      case 'winter':
        return 1; // January
      default:
        return 5; // May (default)
    }
  }
}

