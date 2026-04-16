int? _jsonInt(dynamic v) {
  if (v == null) return null;
  if (v is int) return v;
  if (v is double) return v.round();
  if (v is num) return v.toInt();
  return int.tryParse(v.toString());
}

int _jsonIntNonNull(dynamic v, [int defaultValue = 1]) => _jsonInt(v) ?? defaultValue;

double? _jsonDouble(dynamic v) {
  if (v == null) return null;
  if (v is double) return v;
  if (v is int) return v.toDouble();
  if (v is num) return v.toDouble();
  return double.tryParse(v.toString());
}

enum Mood { adventurous, relaxed, romantic, family, cultural }

extension MoodLabel on Mood {
  String get label {
    switch (this) {
      case Mood.adventurous:
        return 'Adventurous';
      case Mood.relaxed:
        return 'Relaxed';
      case Mood.romantic:
        return 'Romantic';
      case Mood.family:
        return 'Family';
      case Mood.cultural:
        return 'Cultural';
    }
  }
}

class ItineraryFormData {
  final Mood mood;
  final int budget; // approximate budget number in PKR
  final String season; // e.g., Summer, Winter (for backward compatibility)
  final List<String> activities;
  final int durationDays; // 5-7 days typical
  final String? destination; // Optional - will be set when user selects from recommendations
  final int travelMonth; // 1-12 (matches backend format)
  final String? startDate; // Optional start date in YYYY-MM-DD format
  final int numPeople; // Number of people traveling
  /// Set when user picks a multi-city corridor recommendation (RAG agent).
  final int? corridorId;

  const ItineraryFormData({
    required this.mood,
    required this.budget,
    required this.season,
    required this.activities,
    required this.durationDays,
    this.destination,
    required this.travelMonth,
    this.startDate,
    this.numPeople = 1, // Default to 1 person
    this.corridorId,
  });
}

/// Model for destination recommendation from backend
/// Hub rows have [locationId]; corridor rows have [corridorId] instead.
class DestinationRecommendation {
  final int rank;
  final String destination;
  final String region;
  final int? locationId;
  final int? corridorId;
  final double matchScore;
  final RecommendationPreview preview;

  const DestinationRecommendation({
    required this.rank,
    required this.destination,
    required this.region,
    this.locationId,
    this.corridorId,
    required this.matchScore,
    required this.preview,
  });

  bool get isCorridor => corridorId != null;

  factory DestinationRecommendation.fromJson(Map<String, dynamic> json) {
    return DestinationRecommendation(
      rank: (json['rank'] as num?)?.toInt() ?? 0,
      destination: json['destination'] as String? ?? '',
      region: json['region'] as String? ?? '',
      locationId: (json['location_id'] as num?)?.toInt(),
      corridorId: (json['corridor_id'] as num?)?.toInt(),
      matchScore: (json['match_score'] as num?)?.toDouble() ?? 0,
      preview: RecommendationPreview.fromJson(
        json['preview'] as Map<String, dynamic>? ?? <String, dynamic>{},
      ),
    );
  }
}

class RecommendationPreview {
  final String title;
  final List<String> highlights;
  final List<String> activities;
  final Map<String, dynamic>? costEstimate;
  final int poiCount;
  final double? averageRating;

  const RecommendationPreview({
    required this.title,
    required this.highlights,
    required this.activities,
    this.costEstimate,
    required this.poiCount,
    this.averageRating,
  });

  factory RecommendationPreview.fromJson(Map<String, dynamic> json) {
    final highlights = json['highlights'];
    final activities = json['activities'];
    return RecommendationPreview(
      title: json['title'] as String? ?? '',
      highlights: highlights is List
          ? highlights.map((e) => e.toString()).toList()
          : <String>[],
      activities: activities is List
          ? activities.map((e) => e.toString()).toList()
          : <String>[],
      costEstimate: json['cost_estimate'] as Map<String, dynamic>?,
      poiCount: (json['poi_count'] as num?)?.toInt() ?? 0,
      averageRating: json['average_rating'] != null ? (json['average_rating'] as num).toDouble() : null,
    );
  }
}

// ---------------------------------------------------------------------------
// New RAG-based itinerary models (timeline format)
// ---------------------------------------------------------------------------

class TimeSlot {
  final String timeOfDay;
  final String startTime;
  final String endTime;
  final String activityType;
  final int? poiId;
  final String locationName;
  final String description;
  final String estimatedCostPkr;
  final String travelTips;
  final int? transitFromPreviousMins;
  final double? transitDistanceKm;
  final String? transitInstruction;
  /// POI coordinates when provided by the API (Geoapify map / routing).
  final double? latitude;
  final double? longitude;

  const TimeSlot({
    required this.timeOfDay,
    required this.startTime,
    required this.endTime,
    required this.activityType,
    this.poiId,
    required this.locationName,
    required this.description,
    required this.estimatedCostPkr,
    required this.travelTips,
    this.transitFromPreviousMins,
    this.transitDistanceKm,
    this.transitInstruction,
    this.latitude,
    this.longitude,
  });

  bool get hasCoordinates =>
      latitude != null && longitude != null;

  factory TimeSlot.fromJson(Map<String, dynamic> json) {
    return TimeSlot(
      timeOfDay: json['time_of_day'] as String? ?? 'Morning',
      startTime: json['start_time'] as String? ?? '',
      endTime: json['end_time'] as String? ?? '',
      activityType: json['activity_type'] as String? ?? 'Sightseeing',
      poiId: _jsonInt(json['poi_id']),
      locationName: json['location_name'] as String? ?? 'Unknown',
      description: json['description'] as String? ?? '',
      estimatedCostPkr: json['estimated_cost_pkr']?.toString() ?? '0',
      travelTips: json['travel_tips'] as String? ?? '',
      transitFromPreviousMins: _jsonInt(json['transit_from_previous_mins']),
      transitDistanceKm: _jsonDouble(json['transit_distance_km']),
      transitInstruction: json['transit_instruction'] as String?,
      latitude: _jsonDouble(json['latitude']),
      longitude: _jsonDouble(json['longitude']),
    );
  }

  bool get hasTransitInfo =>
      transitFromPreviousMins != null && transitFromPreviousMins! > 0;

  /// Formatted display title, e.g. "Hiking at Rakaposhi Base Camp Trail".
  /// When [locationName] already starts with the activity ("Lunch at …",
  /// "Photography on …"), skips the extra `"$activityType at "` prefix.
  String get displayTitle {
    final act = activityType.trim();
    final loc = locationName.trim();
    if (act.isEmpty) return loc;
    if (loc.isEmpty) return act;
    if (act.toLowerCase() == loc.toLowerCase()) return loc;

    final actLower = act.toLowerCase();
    final locLower = loc.toLowerCase();
    if (locLower.startsWith(actLower)) {
      final rest =
          loc.length >= act.length ? loc.substring(act.length) : '';
      if (rest.isEmpty) return loc;
      if (RegExp(r'^\s+(at|on|in|near|around)\s', caseSensitive: false)
          .hasMatch(rest)) {
        return loc;
      }
    }

    // "Scenic Drive" + "Drive to Baltoro Glacier" — the location already
    // opens with the same head verb as the activity's last word ("Drive").
    final actWords =
        act.split(RegExp(r'\s+')).where((String w) => w.isNotEmpty).toList();
    if (actWords.isNotEmpty) {
      final lastWord = actWords.last.toLowerCase();
      if (lastWord.length >= 3) {
        final firstLoc = RegExp(r'^(\S+)').firstMatch(locLower)?.group(1);
        if (firstLoc != null && firstLoc == lastWord) {
          return loc;
        }
      }
    }

    return '$act at $loc';
  }
}

class DayPlan {
  final int dayNumber;
  final String themeTitle;
  final String daySummary;
  final List<TimeSlot> timeSlots;

  const DayPlan({
    required this.dayNumber,
    required this.themeTitle,
    required this.daySummary,
    required this.timeSlots,
  });

  factory DayPlan.fromJson(Map<String, dynamic> json) {
    final rawSlots = json['time_slots'];
    final List<TimeSlot> slots = [];
    if (rawSlots is List) {
      for (final s in rawSlots) {
        if (s is Map<String, dynamic>) {
          slots.add(TimeSlot.fromJson(s));
        } else if (s is Map) {
          slots.add(TimeSlot.fromJson(Map<String, dynamic>.from(s)));
        }
      }
    }
    final dn = _jsonIntNonNull(json['day_number'], 1);
    return DayPlan(
      dayNumber: dn,
      themeTitle: json['theme_title'] as String? ?? 'Day $dn',
      daySummary: json['day_summary'] as String? ?? '',
      timeSlots: slots,
    );
  }

  /// Single-line heading for app bars: "Day N – …" without repeating "Day N"
  /// when [themeTitle] from the API already includes that prefix.
  String get displayHeading {
    var t = themeTitle.trim();
    if (t.isEmpty) return 'Day $dayNumber';
    final leadingDay = RegExp(
      '^day\\s*$dayNumber\\s*(?:[–\\-—]\\s*)+',
      caseSensitive: false,
    );
    if (leadingDay.hasMatch(t)) {
      t = t.replaceFirst(leadingDay, '').trim();
    }
    if (t.isEmpty) return 'Day $dayNumber';
    return 'Day $dayNumber – $t';
  }
}

class CostRange {
  final int min;
  final int max;

  const CostRange({required this.min, required this.max});

  factory CostRange.fromJson(Map<String, dynamic> json) {
    return CostRange(
      min: _jsonInt(json['min']) ?? 0,
      max: _jsonInt(json['max']) ?? 0,
    );
  }
}

class LocationInfo {
  final double latitude;
  final double longitude;
  final double? elevation;
  final String? climateZone;
  final String? touristSeason;

  const LocationInfo({
    required this.latitude,
    required this.longitude,
    this.elevation,
    this.climateZone,
    this.touristSeason,
  });
}

class TripItinerary {
  final String id;
  final String title;
  final String destination;
  final String region;
  final int days;
  final int totalBudget;
  final int numPeople;
  final String tripOverview;
  final CostRange estimatedCostRange;
  final int? estimatedTransportCostPkr;
  final List<String> packingRecommendations;
  final List<DayPlan> daysPlan;
  final LocationInfo? locationInfo;

  const TripItinerary({
    required this.id,
    required this.title,
    required this.destination,
    required this.region,
    required this.days,
    required this.totalBudget,
    this.numPeople = 1,
    required this.tripOverview,
    required this.estimatedCostRange,
    this.estimatedTransportCostPkr,
    this.packingRecommendations = const [],
    required this.daysPlan,
    this.locationInfo,
  });

  /// Stops with coordinates, in day order then chronological slot order.
  List<TimeSlot> get geoOrderedStops {
    final out = <TimeSlot>[];
    for (final day in daysPlan) {
      for (final slot in day.timeSlots) {
        if (slot.hasCoordinates) out.add(slot);
      }
    }
    return out;
  }
}


