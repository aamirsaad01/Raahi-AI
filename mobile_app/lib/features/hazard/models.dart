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
  final String? advisoryUrl; // For NDMA alerts
  final String? advisoryType; // For NDMA alerts
  final double? distanceKm; // Optional: distance from scan center

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
    this.advisoryUrl,
    this.advisoryType,
    this.distanceKm,
  });

  factory HazardReport.fromJson(Map<String, dynamic> json) {
    return HazardReport(
      id: json['id'] ?? '',
      type: _hazardTypeFromString(json['type'] ?? 'roadblock'),
      severity: _severityFromString(json['severity'] ?? 'low'),
      timestamp: _parseDateTime(json['timestamp']),
      source: json['source'] ?? 'Unknown',
      lat: (json['lat'] as num?)?.toDouble() ?? 0.0,
      lon: (json['lon'] as num?)?.toDouble() ?? 0.0,
      location: json['location'] ?? 'Unknown',
      description: json['description'],
      advisoryUrl: json['advisory_url'],
      advisoryType: json['advisory_type'],
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type.name,
      'severity': severity.name,
      'timestamp': timestamp.toIso8601String(),
      'source': source,
      'lat': lat,
      'lon': lon,
      'location': location,
      'description': description,
      'advisory_url': advisoryUrl,
      'advisory_type': advisoryType,
      'distance_km': distanceKm,
    };
  }

  static HazardType _hazardTypeFromString(String str) {
    switch (str.toLowerCase()) {
      case 'landslide':
        return HazardType.landslide;
      case 'flood':
        return HazardType.flood;
      case 'roadblock':
        return HazardType.roadblock;
      case 'snowfall':
        return HazardType.snowfall;
      case 'protest':
        return HazardType.protest;
      case 'accident':
        return HazardType.accident;
      default:
        return HazardType.roadblock;
    }
  }

  static Severity _severityFromString(String str) {
    switch (str.toLowerCase()) {
      case 'low':
        return Severity.low;
      case 'medium':
        return Severity.medium;
      case 'high':
        return Severity.high;
      case 'critical':
        return Severity.critical;
      default:
        return Severity.low;
    }
  }

  static DateTime _parseDateTime(dynamic value) {
    if (value == null) return DateTime.now();
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (e) {
        return DateTime.now();
      }
    }
    return DateTime.now();
  }
}


