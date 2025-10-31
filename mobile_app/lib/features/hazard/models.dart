enum HazardType { landslide, flood, roadblock, snowfall, protest, accident }

extension HazardTypeLabel on HazardType {
  String get label {
    switch (this) {
      case HazardType.landslide:
        return 'Landslide';
      case HazardType.flood:
        return 'Flood';
      case HazardType.roadblock:
        return 'Roadblock';
      case HazardType.snowfall:
        return 'Snowfall';
      case HazardType.protest:
        return 'Protest';
      case HazardType.accident:
        return 'Accident';
    }
  }
}

enum Severity { low, medium, high, critical }

extension SeverityLabel on Severity {
  String get label {
    switch (this) {
      case Severity.low:
        return 'Low';
      case Severity.medium:
        return 'Medium';
      case Severity.high:
        return 'High';
      case Severity.critical:
        return 'Critical';
    }
  }
}

class HazardReport {
  final String id;
  final HazardType type;
  final Severity severity;
  final DateTime timestamp;
  final String source; // NDMA/PMD/User
  final double lat;
  final double lon;
  final String location;
  final String? description;

  const HazardReport({
    required this.id,
    required this.type,
    required this.severity,
    required this.timestamp,
    required this.source,
    required this.lat,
    required this.lon,
    required this.location,
    this.description,
  });
}


