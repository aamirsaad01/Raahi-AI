import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mobile_app/config/api_config.dart';

import 'models.dart';

class HazardApiService {
  /// Get all hazards (NDMA alerts + user reports)
  /// 
  /// [source] - Filter by source: 'ndma', 'user', 'pmd', or null for all
  /// [severity] - Filter by severity: 'low', 'medium', 'high', 'critical', or null for all
  /// [timeWindow] - Filter by time: '24h', '7d', '1m', 'all'
  Future<List<HazardReport>> getHazards({
    String? source,
    String? severity,
    String timeWindow = 'all',
  }) async {
    try {
      final queryParams = <String, String>{};
      if (source != null) queryParams['source'] = source;
      if (severity != null) queryParams['severity'] = severity;
      queryParams['time_window'] = timeWindow;

      final uri = Uri.parse('${ApiConfig.baseUrl}/api/hazards').replace(queryParameters: queryParams);
      
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> hazardsJson = data['hazards'] ?? [];
          return hazardsJson.map((json) => HazardReport.fromJson(json)).toList();
        } else {
          throw Exception(data['error'] ?? 'Failed to fetch hazards');
        }
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to fetch hazards');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Submit a new hazard report.
  /// If [latitude] and [longitude] are both set, those coordinates are stored;
  /// otherwise the backend geocodes [location] (Geoapify / OSM).
  Future<Map<String, dynamic>> reportHazard({
    required HazardType type,
    required Severity severity,
    required String location,
    required String title,
    String? description,
    double? latitude,
    double? longitude,
  }) async {
    try {
      final Map<String, dynamic> payload = {
        'type': _hazardTypeToBackend(type),
        'severity': severity.name,
        'location': location,
        'title': title,
        'description': description,
      };
      if (latitude != null && longitude != null) {
        payload['latitude'] = latitude;
        payload['longitude'] = longitude;
      }
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/api/hazards/report'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return data;
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to report hazard');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Get user's reported hazards
  Future<List<HazardReport>> getMyReports() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/api/hazards/my-reports'),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          final List<dynamic> hazardsJson = data['hazards'] ?? [];
          return hazardsJson.map((json) => HazardReport.fromJson(json)).toList();
        } else {
          throw Exception(data['error'] ?? 'Failed to fetch reports');
        }
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to fetch reports');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Refresh hazards by triggering NDMA scraper
  /// This will fetch latest advisories from NDMA website
  Future<Map<String, dynamic>> refreshHazards() async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/api/hazards/refresh'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data;
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['error'] ?? 'Failed to refresh hazards');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  String _hazardTypeToBackend(HazardType type) {
    switch (type) {
      case HazardType.landslide:
        return 'landslide';
      case HazardType.flood:
        return 'flood';
      case HazardType.roadblock:
        return 'roadblock';
      case HazardType.snowfall:
        return 'snowfall';
      case HazardType.protest:
        return 'protest';
      case HazardType.accident:
        return 'accident';
    }
  }
}



