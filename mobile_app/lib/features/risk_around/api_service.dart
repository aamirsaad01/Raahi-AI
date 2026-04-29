import 'dart:convert';
import 'package:http/http.dart' as http;
import '../hazard/models.dart';

class RiskAroundApiService {
  static const String baseUrl = 'https://coronary-haste-zombie.ngrok-free.dev';

  Future<List<HazardReport>> scanNearbyHazards({
    required double lat,
    required double lon,
    double radiusKm = 5,
  }) async {
    final uri = Uri.parse('$baseUrl/api/hazards/nearby').replace(
      queryParameters: <String, String>{
        'lat': lat.toString(),
        'lon': lon.toString(),
        'radius_km': radiusKm.toString(),
      },
    );
    final response = await http.get(uri);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final rows = body['hazards'] as List<dynamic>? ?? <dynamic>[];
      return rows
          .map((dynamic e) => HazardReport.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    throw Exception(body['error'] ?? 'Failed to scan nearby hazards');
  }
}

