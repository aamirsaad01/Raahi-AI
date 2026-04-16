import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';

/// Fetches road / trail geometry from Geoapify Routing API (GeoJSON).
///
/// Uses **one request per consecutive pair of stops** so each map segment follows
/// real routes. Multi-stop single requests are brittle (long URLs, failures).
class GeoapifyRouteClient {
  const GeoapifyRouteClient();

  /// Builds a continuous path from first to last stop along drivable or hiking
  /// routes. Falls back to a two-point straight segment only for hops where
  /// Geoapify returns no geometry.
  Future<List<LatLng>?> fetchConnectedRoutePolyline({
    required List<LatLng> waypoints,
    required String apiKey,
  }) async {
    if (waypoints.length < 2) return <LatLng>[];
    if (apiKey.isEmpty) return null;

    final merged = <LatLng>[];
    for (var i = 0; i < waypoints.length - 1; i++) {
      final from = waypoints[i];
      final to = waypoints[i + 1];
      final segment = await _fetchSegmentBestEffort(from, to, apiKey);

      if (segment != null && segment.length >= 2) {
        if (merged.isEmpty) {
          merged.addAll(segment);
        } else if (_samePoint(merged.last, segment.first)) {
          merged.addAll(segment.skip(1));
        } else {
          merged.addAll(segment);
        }
      } else {
        if (merged.isEmpty) merged.add(from);
        merged.add(to);
      }
    }
    return merged;
  }

  /// Prefer driving roads; for gaps with no drive network (e.g. glaciers),
  /// [hike] often still returns a trail-like path on OSM where available.
  Future<List<LatLng>?> _fetchSegmentBestEffort(
    LatLng from,
    LatLng to,
    String apiKey,
  ) async {
    for (final mode in const ['drive', 'hike']) {
      final pts = await _requestTwoPointRoute(from, to, apiKey, mode);
      if (pts != null && pts.length >= 2) return pts;
    }
    return null;
  }

  Future<List<LatLng>?> _requestTwoPointRoute(
    LatLng a,
    LatLng b,
    String apiKey,
    String mode,
  ) async {
    final wp = '${a.latitude},${a.longitude}|${b.latitude},${b.longitude}';
    final uri = Uri.https('api.geoapify.com', '/v1/routing', <String, String>{
      'waypoints': wp,
      'mode': mode,
      'format': 'geojson',
      'apiKey': apiKey,
    });

    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 25));
      if (response.statusCode != 200) {
        return null;
      }
      final data = jsonDecode(response.body);
      return _geometryToPoints(data);
    } catch (_) {
      return null;
    }
  }

  /// Accepts full GeoJSON FeatureCollection or a single Feature map.
  static List<LatLng>? _geometryToPoints(dynamic data) {
    if (data is! Map<String, dynamic>) return null;

    List<dynamic>? features;
    if (data['type'] == 'FeatureCollection') {
      features = data['features'] as List<dynamic>?;
    } else if (data['type'] == 'Feature') {
      features = [data];
    } else if (data['features'] is List) {
      features = data['features'] as List<dynamic>;
    }

    if (features == null || features.isEmpty) return null;

    for (final raw in features) {
      if (raw is! Map<String, dynamic>) continue;
      final geom = raw['geometry'];
      if (geom is! Map<String, dynamic>) continue;
      final pts = _pointsFromGeometry(geom);
      if (pts != null && pts.length >= 2) return pts;
    }
    return null;
  }

  static List<LatLng>? _pointsFromGeometry(Map<String, dynamic> geom) {
    final typ = geom['type'] as String?;
    final coords = geom['coordinates'];
    if (typ == 'LineString' && coords is List) {
      return _lineStringPairs(coords);
    }
    if (typ == 'MultiLineString' && coords is List) {
      final out = <LatLng>[];
      for (final line in coords) {
        if (line is List) out.addAll(_lineStringPairs(line));
      }
      return out.length >= 2 ? out : null;
    }
    return null;
  }

  /// GeoJSON positions are [longitude, latitude] (optional elevation).
  static List<LatLng> _lineStringPairs(List<dynamic> coordinates) {
    final out = <LatLng>[];
    for (final pair in coordinates) {
      if (pair is List && pair.length >= 2 && pair[0] is num && pair[1] is num) {
        final lon = (pair[0] as num).toDouble();
        final lat = (pair[1] as num).toDouble();
        out.add(LatLng(lat, lon));
      }
    }
    return out;
  }

  static bool _samePoint(LatLng a, LatLng b) =>
      a.latitude == b.latitude && a.longitude == b.longitude;

  /// Straight vertices only — used when no API key (caller).
  static List<LatLng> straightLineThrough(List<LatLng> waypoints) =>
      List<LatLng>.from(waypoints);
}
