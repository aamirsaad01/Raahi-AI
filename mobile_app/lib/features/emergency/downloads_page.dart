import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import '../../utils/app_constants.dart';
import '../auth/auth_session.dart';
import '../hazard/api_service.dart';
import '../hazard/models.dart';
import '../itinerary/api_service.dart';
import '../itinerary/models.dart';
import 'safe_points_api_service.dart';

class EmergencyDownloadsPage extends StatefulWidget {
  const EmergencyDownloadsPage({super.key});

  @override
  State<EmergencyDownloadsPage> createState() => _EmergencyDownloadsPageState();
}

class _EmergencyDownloadsPageState extends State<EmergencyDownloadsPage> {
  final HazardApiService _hazardApi = HazardApiService();
  final SafePointsApiService _safePointsApi = SafePointsApiService();
  final ItineraryApiService _itineraryApi = ItineraryApiService();
  bool _downloading = false;
  String? _status;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offline Downloads')),
      body: ListView(
        padding: const EdgeInsets.all(16).add(AppConstants.footerPadding),
        children: <Widget>[
          _Tile(title: 'Northern Region Tiles', progress: 0.7),
          _Tile(title: 'Safe Points POIs', progress: 1.0),
          _Tile(title: 'Latest Hazard Data', progress: 0.35),
          const SizedBox(height: 16),
          if (_status != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Text(_status!),
            ),
          FilledButton.icon(
            onPressed: _downloading ? null : _downloadData,
            icon: const Icon(Icons.download_rounded),
            label: Text(_downloading ? 'Downloading...' : 'Download Data'),
          ),
        ],
      ),
    );
  }

  Future<void> _downloadData() async {
    setState(() {
      _downloading = true;
      _status = 'Preparing download...';
    });
    try {
      final user = await AuthSession.load();
      if (user == null) {
        throw Exception('Please login first.');
      }

      setState(() => _status = 'Fetching latest itinerary...');
      final List<TripItinerary> itineraries = await _itineraryApi.getUserItineraries(
        user.userId,
      );
      if (itineraries.isEmpty) {
        throw Exception('No itinerary found for this user.');
      }
      final TripItinerary latest = itineraries.first;
      final String city = latest.destination.trim();
      if (city.isEmpty) {
        throw Exception('Latest itinerary has no destination city.');
      }

      setState(() => _status = 'Fetching hazards and safe points...');
      final List<HazardReport> hazards = await _hazardApi.getHazards(
        timeWindow: 'all',
      );
      final List<SafePoint> safePoints = await _safePointsApi.fetchByCity(city);

      final Directory outDir = await _resolveOutputDirectory();
      final String safeCity = city.replaceAll(RegExp(r'[^a-zA-Z0-9_-]'), '_');
      final File hazardFile = File(
        '${outDir.path}/hazards_${safeCity}_${DateTime.now().millisecondsSinceEpoch}.csv',
      );
      final File safePointsFile = File(
        '${outDir.path}/safe_points_${safeCity}_${DateTime.now().millisecondsSinceEpoch}.csv',
      );

      setState(() => _status = 'Writing CSV files...');
      await hazardFile.writeAsString(_hazardsToCsv(hazards));
      await safePointsFile.writeAsString(_safePointsToCsv(safePoints));

      if (!mounted) return;
      setState(() {
        _status =
            'Saved:\n${hazardFile.path}\n${safePointsFile.path}';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Offline CSV files saved to: ${outDir.path}')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = 'Download failed: ${e.toString().replaceFirst('Exception: ', '')}');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_status!)),
      );
    } finally {
      if (mounted) setState(() => _downloading = false);
    }
  }

  String _csvCell(String value) {
    final String escaped = value.replaceAll('"', '""');
    return '"$escaped"';
  }

  String _hazardsToCsv(List<HazardReport> rows) {
    final StringBuffer sb = StringBuffer();
    sb.writeln(
      'id,type,severity,timestamp,source,location,lat,lon,description,advisory_type,advisory_url',
    );
    for (final HazardReport h in rows) {
      sb.writeln([
        _csvCell(h.id),
        _csvCell(h.type.name),
        _csvCell(h.severity.name),
        _csvCell(h.timestamp.toIso8601String()),
        _csvCell(h.source),
        _csvCell(h.location),
        h.lat.toString(),
        h.lon.toString(),
        _csvCell(h.description ?? ''),
        _csvCell(h.advisoryType ?? ''),
        _csvCell(h.advisoryUrl ?? ''),
      ].join(','));
    }
    return sb.toString();
  }

  String _safePointsToCsv(List<SafePoint> rows) {
    final StringBuffer sb = StringBuffer();
    sb.writeln('safe_point_id,city,name,category,location,latitude,longitude,distance_km');
    for (final SafePoint p in rows) {
      sb.writeln([
        p.safePointId.toString(),
        _csvCell(p.city),
        _csvCell(p.name),
        _csvCell(p.category),
        _csvCell(p.location),
        p.latitude.toString(),
        p.longitude.toString(),
        (p.distanceKm ?? 0).toString(),
      ].join(','));
    }
    return sb.toString();
  }

  Future<Directory> _resolveOutputDirectory() async {
    // Prefer user-visible Downloads on Android for demo/evaluation.
    if (Platform.isAndroid) {
      final Directory downloads = Directory('/storage/emulated/0/Download');
      if (await downloads.exists()) {
        return downloads;
      }
      final Directory? external = await getExternalStorageDirectory();
      if (external != null) {
        return external;
      }
    }

    // iOS + fallback: app documents directory.
    final Directory docs = await getApplicationDocumentsDirectory();
    return docs;
  }
}

class _Tile extends StatelessWidget {
  final String title;
  final double progress;
  const _Tile({required this.title, required this.progress});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(title, style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            LinearProgressIndicator(value: progress),
          ],
        ),
      ),
    );
  }
}


