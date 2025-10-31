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
  final String season; // e.g., Summer, Winter
  final List<String> activities;
  final int durationDays; // 5-7 days typical

  const ItineraryFormData({
    required this.mood,
    required this.budget,
    required this.season,
    required this.activities,
    required this.durationDays,
  });
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

  const Poi({
    required this.id,
    required this.name,
    required this.region,
    this.description,
    this.photos = const <String>[],
    required this.bestSeason,
    required this.activityType,
    required this.difficulty,
  });
}

class DayPlan {
  final int dayNumber;
  final List<Poi> stops;
  final String? notes;

  const DayPlan({required this.dayNumber, required this.stops, this.notes});
}

class TripItinerary {
  final String id;
  final String title;
  final List<DayPlan> days;
  final int estimatedCost;
  final List<String> highlights;

  const TripItinerary({
    required this.id,
    required this.title,
    required this.days,
    required this.estimatedCost,
    required this.highlights,
  });
}

class CostBreakdown {
  final int transport;
  final int stay;
  final int food;
  final int activities;

  const CostBreakdown({
    required this.transport,
    required this.stay,
    required this.food,
    required this.activities,
  });

  int get total => transport + stay + food + activities;
}


