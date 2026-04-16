import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models.dart';

class ItineraryApiService {
  // Change this to your backend URL
  // For local testing: 'http://localhost:5000' or 'http://127.0.0.1:5000'
  // For Android emulator: 'http://10.0.2.2:5000'
  static const String baseUrl = 'https://coronary-haste-zombie.ngrok-free.dev'; // TODO: Paste the HTTPS Ngrok link here

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
    int? corridorId,
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
        if (corridorId != null) 'corridor_id': corridorId,
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

  /// Parse backend response to TripItinerary model.
  /// Handles both the new RAG-based schema (days→time_slots) and
  /// the legacy rule-based schema (daily_plan→pois) for backward compat.
  TripItinerary _parseItineraryResponse(Map<String, dynamic> data) {
    // Detect schema: the RAG agent returns `itinerary_title` + `days` as a
    // JSON array of day objects.  The legacy generator returns `title` +
    // `daily_plan` and `days` as an integer count.
    final bool isRagSchema = data.containsKey('itinerary_title') ||
        (data['days'] is List);

    final List<DayPlan> parsedDays = [];

    if (isRagSchema) {
      // `days` is the LLM-generated list of day objects
      final rawDays = (data['days'] is List) ? data['days'] as List<dynamic> : <dynamic>[];
      for (final d in rawDays) {
        if (d is Map<String, dynamic>) {
          parsedDays.add(DayPlan.fromJson(d));
        } else if (d is Map) {
          parsedDays.add(DayPlan.fromJson(Map<String, dynamic>.from(d)));
        }
      }
    } else {
      // Legacy: convert old daily_plan → new DayPlan shape
      final dailyPlan = data['daily_plan'] as List<dynamic>? ?? [];
      for (final dayData in dailyPlan) {
        final pois = dayData['pois'] as List<dynamic>? ?? [];
        final slots = pois.map<TimeSlot>((p) {
          return TimeSlot(
            timeOfDay: _timeOfDayFromHour(p['time'] as String?),
            startTime: p['time'] as String? ?? '',
            endTime: '',
            activityType: p['category'] as String? ?? 'General',
            poiId: p['poi_id'] as int?,
            locationName: p['name'] as String? ?? 'Unknown',
            description: p['description'] as String? ?? '',
            estimatedCostPkr: (p['cost'] ?? 0).toString(),
            travelTips: '',
            latitude: p['latitude'] != null ? _toDouble(p['latitude']) : null,
            longitude: p['longitude'] != null ? _toDouble(p['longitude']) : null,
          );
        }).toList();

        parsedDays.add(DayPlan(
          dayNumber: (dayData['day'] as num?)?.toInt() ?? 1,
          themeTitle: 'Day ${(dayData['day'] as num?)?.toInt() ?? 1}',
          daySummary: dayData['summary'] as String? ?? '',
          timeSlots: slots,
        ));
      }
    }

    // Parse cost range (RAG: {min,max}, single number, or legacy fallback)
    final tec = data['total_estimated_cost_pkr'];
    CostRange costRange;
    if (tec is Map) {
      costRange = CostRange.fromJson(Map<String, dynamic>.from(tec));
    } else if (tec is num) {
      final v = tec.toInt();
      costRange = CostRange(min: v, max: v);
    } else if (tec is String && tec.trim().isNotEmpty) {
      final v = int.tryParse(tec.trim()) ?? double.tryParse(tec.trim())?.toInt() ?? 0;
      costRange = CostRange(min: v, max: v);
    } else {
      final est = _toInt(data['cost_breakdown']?['total_estimated'] ?? data['total_budget'] ?? 0);
      costRange = CostRange(min: est, max: est);
    }

    // Packing recommendations
    final packing = (data['packing_recommendations'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .toList() ??
        [];

    // Trip overview
    final overview = data['trip_overview'] as String? ?? '';

    // Location info
    final locData = data['location_info'] as Map<String, dynamic>?;
    LocationInfo? locationInfo;
    if (locData != null) {
      locationInfo = LocationInfo(
        latitude: _toDouble(locData['latitude'] ?? 0),
        longitude: _toDouble(locData['longitude'] ?? 0),
        elevation: locData['elevation'] != null ? _toDouble(locData['elevation']) : null,
        climateZone: locData['climate_zone'] as String?,
        touristSeason: locData['tourist_season'] as String?,
      );
    }

    final int daysCount = parsedDays.isNotEmpty
        ? parsedDays.length
        : _toInt(data['num_days'] ?? (data['days'] is int ? data['days'] : 0));

    final int totalBudget = _toInt(data['total_budget'] ?? data['budget'] ?? 0);

    return TripItinerary(
      id: data['itinerary_id']?.toString() ?? data['id']?.toString() ?? '0',
      title: data['itinerary_title'] as String? ?? data['title'] as String? ?? 'Untitled',
      destination: data['destination'] as String? ?? 'Unknown',
      region: data['region'] as String? ?? 'Unknown',
      days: daysCount,
      totalBudget: totalBudget,
      numPeople: (data['num_people'] as num?)?.toInt() ?? 1,
      tripOverview: overview,
      estimatedCostRange: costRange,
      estimatedTransportCostPkr: _toIntNullable(data['estimated_transport_cost_pkr']),
      packingRecommendations: packing,
      daysPlan: parsedDays,
      locationInfo: locationInfo,
    );
  }

  double _toDouble(dynamic value) {
    if (value is int) return value.toDouble();
    if (value is double) return value;
    if (value is num) return value.toDouble();
    return 0.0;
  }

  int _toInt(dynamic value) {
    if (value == null) return 0;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is num) return value.toInt();
    if (value is String) {
      final t = value.trim();
      if (t.isEmpty) return 0;
      return int.tryParse(t) ?? double.tryParse(t)?.toInt() ?? 0;
    }
    return int.tryParse(value.toString()) ?? 0;
  }

  int? _toIntNullable(dynamic value) {
    if (value == null) return null;
    if (value is int) return value;
    if (value is double) return value.toInt();
    if (value is num) return value.toInt();
    if (value is String) {
      final t = value.trim();
      if (t.isEmpty) return null;
      return int.tryParse(t) ?? double.tryParse(t)?.toInt();
    }
    return int.tryParse(value.toString());
  }

  String _timeOfDayFromHour(String? time) {
    if (time == null || time.isEmpty) return 'Morning';
    final hour = int.tryParse(time.split(':').first) ?? 9;
    if (hour < 12) return 'Morning';
    if (hour < 17) return 'Afternoon';
    return 'Evening';
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

