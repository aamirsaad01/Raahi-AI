import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import 'geoapify_config.dart';
import 'geoapify_route_client.dart';
import 'models.dart';

/// Default center (Pakistan) when no coordinates exist.
const LatLng _kDefaultCenter = LatLng(30.3753, 69.3451);

class RoutesMapPage extends StatefulWidget {
  final TripItinerary itinerary;

  const RoutesMapPage({super.key, required this.itinerary});

  @override
  State<RoutesMapPage> createState() => _RoutesMapPageState();
}

class _RoutesMapPageState extends State<RoutesMapPage> {
  late Future<_MapReadyData> _future;

  @override
  void initState() {
    super.initState();
    _future = _loadMapData(widget.itinerary);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Route Map')),
      body: FutureBuilder<_MapReadyData>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text('Could not load map: ${snapshot.error}'),
              ),
            );
          }
          final data = snapshot.data!;
          if (!data.hasAnyPoint) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'No map points yet. Generate a new itinerary so stops include '
                  'POI coordinates, or open this trip after the backend has been updated.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          return Stack(
            children: [
              if (!kHasGeoapifyKey && data.polylinePoints.length >= 2)
                Positioned(
                  left: 8,
                  right: 8,
                  top: 8,
                  child: Material(
                    color: Theme.of(context).colorScheme.errorContainer,
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.all(10),
                      child: Text(
                        'Road routing needs GEOAPIFY_API_KEY at build time '
                        '(flutter run --dart-define=...). Showing straight lines between stops.',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onErrorContainer,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
                ),
              FlutterMap(
                options: MapOptions(
                  initialCenter: data.initialCenter,
                  initialZoom: data.initialZoom,
                  initialCameraFit: data.initialFit,
                  minZoom: 3,
                  maxZoom: 18,
                  interactionOptions: const InteractionOptions(
                    flags: InteractiveFlag.all,
                  ),
                ),
                children: [
                  TileLayer(
                    urlTemplate: data.tileUrlTemplate,
                    userAgentPackageName: 'com.raahi.mobile_app',
                  ),
                  if (data.polylinePoints.length >= 2)
                    PolylineLayer(
                      polylines: [
                        Polyline(
                          points: data.polylinePoints,
                          strokeWidth: 4,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                      ],
                    ),
                  MarkerLayer(markers: data.markers),
                ],
              ),
              Positioned(
                left: 8,
                right: 8,
                bottom: 8,
                child: _MapAttribution(
                  useGeoapifyTiles: kHasGeoapifyKey,
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _MapAttribution extends StatelessWidget {
  const _MapAttribution({required this.useGeoapifyTiles});

  final bool useGeoapifyTiles;

  @override
  Widget build(BuildContext context) {
    final text = useGeoapifyTiles
        ? '© OpenStreetMap © Geoapify'
        : '© OpenStreetMap contributors';
    return Material(
      color: Colors.black54,
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        child: Text(
          text,
          style: const TextStyle(color: Colors.white70, fontSize: 11),
        ),
      ),
    );
  }
}

class _MapReadyData {
  _MapReadyData({
    required this.initialCenter,
    required this.initialZoom,
    this.initialFit,
    required this.polylinePoints,
    required this.markers,
    required this.tileUrlTemplate,
    required this.hasAnyPoint,
  });

  /// When non-null, [initialCenter]/[initialZoom] are ignored for the first frame.
  final CameraFit? initialFit;
  final LatLng initialCenter;
  final double initialZoom;
  final List<LatLng> polylinePoints;
  final List<Marker> markers;
  final String tileUrlTemplate;
  final bool hasAnyPoint;
}

Future<_MapReadyData> _loadMapData(TripItinerary it) async {
  final stops = it.geoOrderedStops;
  final waypoints = _dedupeConsecutive(
    stops.map((s) => LatLng(s.latitude!, s.longitude!)).toList(),
  );

  final fallback = it.locationInfo;
  final LatLng center = waypoints.isNotEmpty
      ? waypoints.first
      : (fallback != null
          ? LatLng(fallback.latitude, fallback.longitude)
          : _kDefaultCenter);

  if (waypoints.isEmpty) {
    final hasLoc = fallback != null;
    return _MapReadyData(
      initialCenter: center,
      initialZoom: hasLoc ? 8 : 6,
      initialFit: null,
      polylinePoints: const [],
      markers: hasLoc
          ? <Marker>[
              Marker(
                point: center,
                width: 40,
                height: 40,
                child: Icon(Icons.place, size: 40, color: Colors.blue.shade700),
              ),
            ]
          : const [],
      tileUrlTemplate: _tileUrl(),
      hasAnyPoint: hasLoc,
    );
  }

  final routeClient = const GeoapifyRouteClient();
  List<LatLng> line;
  if (waypoints.length >= 2 && kHasGeoapifyKey) {
    final routed = await routeClient.fetchConnectedRoutePolyline(
      waypoints: waypoints,
      apiKey: kGeoapifyApiKey,
    );
    line = routed ?? GeoapifyRouteClient.straightLineThrough(waypoints);
  } else if (waypoints.length >= 2) {
    line = GeoapifyRouteClient.straightLineThrough(waypoints);
  } else {
    line = waypoints;
  }

  final forBounds = line.isNotEmpty ? line : waypoints;
  final CameraFit? fit = forBounds.length == 1
      ? null
      : CameraFit.bounds(
          bounds: LatLngBounds.fromPoints(forBounds),
          padding: const EdgeInsets.fromLTRB(48, 64, 48, 72),
        );

  final markers = <Marker>[];
  var index = 0;
  for (final slot in stops) {
    index += 1;
    final pt = LatLng(slot.latitude!, slot.longitude!);
    markers.add(
      Marker(
        point: pt,
        width: 36,
        height: 36,
        child: Tooltip(
          message: slot.displayTitle,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Icon(Icons.location_on, size: 36, color: Colors.red.shade700),
              Positioned(
                top: 4,
                child: Text(
                  '$index',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  return _MapReadyData(
    initialCenter: forBounds.first,
    initialZoom: 12,
    initialFit: fit,
    polylinePoints: line,
    markers: markers,
    tileUrlTemplate: _tileUrl(),
    hasAnyPoint: true,
  );
}

String _tileUrl() {
  if (kHasGeoapifyKey) {
    return 'https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png'
        '?apiKey=$kGeoapifyApiKey';
  }
  return 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
}

List<LatLng> _dedupeConsecutive(List<LatLng> pts) {
  if (pts.isEmpty) return pts;
  final out = <LatLng>[pts.first];
  for (var i = 1; i < pts.length; i++) {
    final p = pts[i];
    final last = out.last;
    if (p.latitude != last.latitude || p.longitude != last.longitude) {
      out.add(p);
    }
  }
  return out;
}
