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
  });
}

/// Model for destination recommendation from backend
class DestinationRecommendation {
  final int rank;
  final String destination;
  final String region;
  final int locationId;
  final double matchScore;
  final RecommendationPreview preview;

  const DestinationRecommendation({
    required this.rank,
    required this.destination,
    required this.region,
    required this.locationId,
    required this.matchScore,
    required this.preview,
  });

  factory DestinationRecommendation.fromJson(Map<String, dynamic> json) {
    return DestinationRecommendation(
      rank: json['rank'] as int,
      destination: json['destination'] as String,
      region: json['region'] as String,
      locationId: json['location_id'] as int,
      matchScore: (json['match_score'] as num).toDouble(),
      preview: RecommendationPreview.fromJson(json['preview'] as Map<String, dynamic>),
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
    return RecommendationPreview(
      title: json['title'] as String,
      highlights: (json['highlights'] as List<dynamic>).map((e) => e.toString()).toList(),
      activities: (json['activities'] as List<dynamic>).map((e) => e.toString()).toList(),
      costEstimate: json['cost_estimate'] as Map<String, dynamic>?,
      poiCount: json['poi_count'] as int,
      averageRating: json['average_rating'] != null ? (json['average_rating'] as num).toDouble() : null,
    );
  }
}

class Poi {
  final String id;
  final String name;
  final String region;
  final String? description;
  final List<String> photos;
  final String bestSeason;
  final String activityType;
  final String difficulty;
  final String? time;
  final double? durationHours;
  final double? cost;
  final double? latitude;
  final double? longitude;
  final double? rating;
  final List<String> activities;
  final List<String> highlights;
  final double? matchScore;

  const Poi({
    required this.id,
    required this.name,
    required this.region,
    this.description,
    this.photos = const <String>[],
    required this.bestSeason,
    required this.activityType,
    required this.difficulty,
    this.time,
    this.durationHours,
    this.cost,
    this.latitude,
    this.longitude,
    this.rating,
    this.activities = const <String>[],
    this.highlights = const <String>[],
    this.matchScore,
  });
}

class DayPlan {
  final int dayNumber;
  final String? date;
  final List<Poi> stops;
  final String? notes;
  final double? totalDurationHours;
  final double? estimatedCost;
  final int? activitiesCount;

  const DayPlan({
    required this.dayNumber,
    this.date,
    required this.stops,
    this.notes,
    this.totalDurationHours,
    this.estimatedCost,
    this.activitiesCount,
  });
}

class TripItinerary {
  final String id;
  final String title;
  final String destination;
  final String region;
  final int days;
  final int totalBudget;
  final List<DayPlan> daysPlan;
  final int estimatedCost;
  final List<String> highlights;
  final CostBreakdown? costBreakdown;
  final LocationInfo? locationInfo;
  final int selectedPoisCount;
  final int totalPoisAvailable;

  const TripItinerary({
    required this.id,
    required this.title,
    required this.destination,
    required this.region,
    required this.days,
    required this.totalBudget,
    required this.daysPlan,
    required this.estimatedCost,
    required this.highlights,
    this.costBreakdown,
    this.locationInfo,
    this.selectedPoisCount = 0,
    this.totalPoisAvailable = 0,
  });
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

class CostBreakdown {
  final double totalBudget;
  final double totalEstimated;
  final double remaining;
  final CostBreakdownDetails breakdown;
  final CostPerDay? perDay;

  const CostBreakdown({
    required this.totalBudget,
    required this.totalEstimated,
    required this.remaining,
    required this.breakdown,
    this.perDay,
  });
}

class CostBreakdownDetails {
  final double attractions;
  final double accommodation;
  final double food;
  final double transport;

  const CostBreakdownDetails({
    required this.attractions,
    required this.accommodation,
    required this.food,
    required this.transport,
  });
}

class CostPerDay {
  final double accommodation;
  final double food;

  const CostPerDay({
    required this.accommodation,
    required this.food,
  });
}


