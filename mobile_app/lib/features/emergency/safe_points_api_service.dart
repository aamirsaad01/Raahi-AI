import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mobile_app/config/api_config.dart';

class SafePoint {
  final int safePointId;
  final String city;
  final String name;
  final String category;
  final String location;
  final double latitude;
  final double longitude;
  final double? distanceKm;

  const SafePoint({
    required this.safePointId,
    required this.city,
    required this.name,
    required this.category,
    required this.location,
    required this.latitude,
    required this.longitude,
    this.distanceKm,
  });

  static int _toInt(dynamic v) {
    if (v is int) return v;
    if (v is num) return v.toInt();
    return int.tryParse((v ?? '').toString()) ?? 0;
  }

  static double _toDouble(dynamic v) {
    if (v is double) return v;
    if (v is num) return v.toDouble();
    return double.tryParse((v ?? '').toString()) ?? 0.0;
  }

  factory SafePoint.fromJson(Map<String, dynamic> json) {
    return SafePoint(
      safePointId: _toInt(json['safe_point_id']),
      city: (json['city'] ?? '').toString(),
      name: (json['name'] ?? '').toString(),
      category: (json['category'] ?? '').toString(),
      location: (json['location'] ?? '').toString(),
      latitude: _toDouble(json['latitude']),
      longitude: _toDouble(json['longitude']),
      distanceKm: json['distance_km'] == null
          ? null
          : _toDouble(json['distance_km']),
    );
  }
}

class SafePointsApiService {
  static const String _geoapifyApiKey = String.fromEnvironment(
    'GEOAPIFY_API_KEY',
    defaultValue: '',
  );
  static const String _geoapifyPlacesUrl = 'https://api.geoapify.com/v2/places';

  Future<List<String>> fetchCities() async {
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}/api/safe-points/cities'),
    );
    final Map<String, dynamic> body =
        jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final List<dynamic> raw = body['cities'] as List<dynamic>? ?? <dynamic>[];
      return raw.map((dynamic e) => e.toString()).toList();
    }
    throw Exception(body['error'] ?? 'Failed to fetch cities');
  }

  Future<List<SafePoint>> fetchByCity(String city) async {
    final uri = Uri.parse(
      '${ApiConfig.baseUrl}/api/safe-points',
    ).replace(queryParameters: <String, String>{'city': city});
    final response = await http.get(uri);
    final Map<String, dynamic> body =
        jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final List<dynamic> raw =
          body['safe_points'] as List<dynamic>? ?? <dynamic>[];
      return raw
          .whereType<Map<String, dynamic>>()
          .map(SafePoint.fromJson)
          .toList();
    }
    throw Exception(body['error'] ?? 'Failed to fetch safe points');
  }

  Future<List<SafePoint>> fetchNearby({
    required double latitude,
    required double longitude,
    double radiusKm = 5.0,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/safe-points/nearby').replace(
      queryParameters: <String, String>{
        'lat': latitude.toString(),
        'lon': longitude.toString(),
        'radius_km': radiusKm.toString(),
      },
    );
    final response = await http.get(uri);
    final Map<String, dynamic> body =
        jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final List<dynamic> raw =
          body['safe_points'] as List<dynamic>? ?? <dynamic>[];
      return raw
          .whereType<Map<String, dynamic>>()
          .map(SafePoint.fromJson)
          .toList();
    }
    throw Exception(body['error'] ?? 'Failed to fetch nearby safe points');
  }

  Future<List<SafePoint>> fetchNearbyLiveGeoapify({
    required double latitude,
    required double longitude,
    double radiusKm = 5.0,
  }) async {
    if (_geoapifyApiKey.isEmpty) {
      throw Exception(
        'Geoapify key is missing. Run with --dart-define=GEOAPIFY_API_KEY=...',
      );
    }

    const Map<String, List<String>> categoryMap = <String, List<String>>{
      'hospital': <String>['healthcare.hospital'],
      'police station': <String>['service.police'],
      'fuel station': <String>['service.vehicle.fuel'],
      'car workshop': <String>['service.vehicle.repair'],
    };

    final int radiusMeters = (radiusKm * 1000).round().clamp(100, 50000);
    final Map<String, SafePoint> deduped = <String, SafePoint>{};
    int syntheticId = 1;

    final List<String> categoryErrors = <String>[];
    for (final MapEntry<String, List<String>> entry in categoryMap.entries) {
      final String appCategory = entry.key;
      final String geoapifyCategories = entry.value.join(',');
      final Uri uri = Uri.parse(_geoapifyPlacesUrl).replace(
        queryParameters: <String, String>{
          'categories': geoapifyCategories,
          'filter': 'circle:$longitude,$latitude,$radiusMeters',
          'bias': 'proximity:$longitude,$latitude',
          'limit': '80',
          'apiKey': _geoapifyApiKey,
        },
      );

      final http.Response response = await http.get(uri);
      if (response.statusCode != 200) {
        categoryErrors.add('$appCategory (${response.statusCode})');
        continue;
      }

      final Map<String, dynamic> body =
          jsonDecode(response.body) as Map<String, dynamic>;
      final List<dynamic> features =
          body['features'] as List<dynamic>? ?? <dynamic>[];
      for (final dynamic item in features) {
        if (item is! Map<String, dynamic>) continue;
        final Map<String, dynamic> props =
            (item['properties'] as Map?)?.cast<String, dynamic>() ??
            <String, dynamic>{};
        final Map<String, dynamic> geometry =
            (item['geometry'] as Map?)?.cast<String, dynamic>() ??
            <String, dynamic>{};
        final List<dynamic> coords =
            geometry['coordinates'] as List<dynamic>? ?? <dynamic>[];
        if (coords.length < 2) continue;
        final double lon = (coords[0] as num?)?.toDouble() ?? 0;
        final double lat = (coords[1] as num?)?.toDouble() ?? 0;
        if (lat == 0 && lon == 0) continue;

        final String uniqueKey = (props['place_id'] ?? '$appCategory-$lat-$lon')
            .toString();
        final String name = (props['name'] ?? props['address_line1'] ?? 'Unnamed')
            .toString();
        final String location = (props['formatted'] ??
                props['address_line2'] ??
                props['address_line1'] ??
                '')
            .toString();
        final double? distance = (props['distance'] as num?)?.toDouble();

        deduped[uniqueKey] = SafePoint(
          safePointId: syntheticId++,
          city: (props['city'] ?? '').toString(),
          name: name,
          category: appCategory,
          location: location,
          latitude: lat,
          longitude: lon,
          distanceKm: distance == null ? null : distance / 1000.0,
        );
      }
    }

    final List<SafePoint> list = deduped.values.toList();
    list.sort((SafePoint a, SafePoint b) {
      final double da = a.distanceKm ?? 9999;
      final double db = b.distanceKm ?? 9999;
      return da.compareTo(db);
    });
    if (list.isEmpty && categoryErrors.isNotEmpty) {
      throw Exception(
        'Geoapify nearby fetch failed for categories: ${categoryErrors.join(', ')}',
      );
    }
    return list;
  }
}
