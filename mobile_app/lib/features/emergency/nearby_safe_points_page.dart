import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../utils/app_constants.dart';
import 'safe_points_api_service.dart';

class NearbySafePointsPage extends StatefulWidget {
  const NearbySafePointsPage({super.key});

  @override
  State<NearbySafePointsPage> createState() => _NearbySafePointsPageState();
}

class _NearbySafePointsPageState extends State<NearbySafePointsPage> {
  final SafePointsApiService _service = SafePointsApiService();
  bool _loading = true;
  String? _error;
  List<SafePoint> _points = <SafePoint>[];
  double? _lat;
  double? _lon;
  static const double _radiusKm = 5.0;

  @override
  void initState() {
    super.initState();
    _loadNearby();
  }

  Future<void> _loadNearby() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final Position pos = await _getLiveLocation();
      final List<SafePoint> rows = await _service.fetchNearbyLiveGeoapify(
        latitude: pos.latitude,
        longitude: pos.longitude,
        radiusKm: _radiusKm,
      );
      if (!mounted) return;
      setState(() {
        _lat = pos.latitude;
        _lon = pos.longitude;
        _points = rows;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<Position> _getLiveLocation() async {
    final bool enabled = await Geolocator.isLocationServiceEnabled();
    if (!enabled) throw Exception('Location services are disabled.');

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw Exception('Location permission denied.');
    }

    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
        ),
      ).timeout(const Duration(seconds: 12));
    } catch (_) {
      final Position? last = await Geolocator.getLastKnownPosition();
      if (last != null) return last;
      rethrow;
    }
  }

  Future<void> _openMaps(SafePoint p) async {
    final Uri mapsUri = Uri.parse(
      'https://maps.google.com/?q=${p.latitude},${p.longitude}',
    );
    if (!await launchUrl(mapsUri, mode: LaunchMode.externalApplication)) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open Google Maps.')),
      );
    }
  }

  Color _distanceChipColor(double d, ColorScheme cs) {
    if (d <= 1) return Colors.red.shade100;
    if (d <= 3) return Colors.orange.shade100;
    return Colors.amber.shade100;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nearby Safe Points (5 km)')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text('Failed to fetch nearby safe points.\n$_error'),
                    const SizedBox(height: 12),
                    FilledButton(
                      onPressed: _loadNearby,
                      child: const Text('Try Again'),
                    ),
                  ],
                ),
              ),
            )
          : RefreshIndicator(
              onRefresh: _loadNearby,
              child: ListView(
                padding: EdgeInsets.all(16).add(AppConstants.footerScrollInsets(context)),
                children: <Widget>[
                  if (_lat != null && _lon != null)
                    Text(
                      'Your location: ${_lat!.toStringAsFixed(5)}, ${_lon!.toStringAsFixed(5)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  const SizedBox(height: 8),
                  Text('Found ${_points.length} safe points'),
                  const SizedBox(height: 10),
                  if (_points.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(14),
                        child: Text('No safe points found within 5 km.'),
                      ),
                    ),
                  ..._points.map((SafePoint p) {
                    final double d = p.distanceKm ?? 0;
                    return Card(
                      child: ListTile(
                        onTap: () => _openMaps(p),
                        leading: const Icon(Icons.place_rounded),
                        title: Text(p.name),
                        subtitle: Text('${p.category} • ${p.location}'),
                        trailing: Chip(
                          label: Text('${d.toStringAsFixed(1)} km'),
                          backgroundColor: _distanceChipColor(
                            d,
                            Theme.of(context).colorScheme,
                          ),
                        ),
                      ),
                    );
                  }),
                ],
              ),
            ),
    );
  }
}
