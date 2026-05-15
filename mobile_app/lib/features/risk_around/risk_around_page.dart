import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../../utils/app_constants.dart';
import '../hazard/hazard_detail_sheet.dart';
import '../hazard/models.dart';
import 'api_service.dart';

class RiskAroundPage extends StatefulWidget {
  const RiskAroundPage({super.key});

  @override
  State<RiskAroundPage> createState() => _RiskAroundPageState();
}

class _RiskAroundPageState extends State<RiskAroundPage> {
  final RiskAroundApiService _api = RiskAroundApiService();
  bool _isScanning = false;
  String? _error;
  List<HazardReport> _hazards = <HazardReport>[];
  Position? _lastPosition;

  Future<void> _scanRisk() async {
    setState(() {
      _isScanning = true;
      _error = null;
    });
    try {
      final pos = await _getLiveLocation();
      final hazards = await _api.scanNearbyHazards(
        lat: pos.latitude,
        lon: pos.longitude,
        radiusKm: 5,
      );
      if (!mounted) return;
      setState(() {
        _lastPosition = pos;
        _hazards = hazards;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isScanning = false);
    }
  }

  Future<Position> _getLiveLocation() async {
    final enabled = await Geolocator.isLocationServiceEnabled();
    if (!enabled) throw Exception('Location service is disabled.');
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw Exception('Location permission denied.');
    }
    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
      ).timeout(const Duration(seconds: 12));
    } catch (_) {
      final last = await Geolocator.getLastKnownPosition();
      if (last != null) return last;
      rethrow;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Risk Around Me')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _isScanning ? null : _scanRisk,
                icon: const Icon(Icons.radar_rounded),
                label: Text(_isScanning ? 'Scanning...' : 'Scan Risk Around You'),
              ),
            ),
          ),
          if (_lastPosition != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Location: ${_lastPosition!.latitude.toStringAsFixed(5)}, '
                  '${_lastPosition!.longitude.toStringAsFixed(5)}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ),
          const SizedBox(height: 8),
          Expanded(child: _buildBody(context)),
        ],
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    if (_isScanning && _hazards.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 56, color: Colors.red),
              const SizedBox(height: 12),
              Text(_error!, textAlign: TextAlign.center),
            ],
          ),
        ),
      );
    }
    if (_hazards.isEmpty) {
      return Center(
        child: Text(
          'No hazards found within 5 km.\nTap "Scan Risk Around You".',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      );
    }
    return ListView.separated(
      padding: EdgeInsets.all(12).add(AppConstants.footerScrollInsets(context)),
      itemCount: _hazards.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (BuildContext context, int i) {
        final r = _hazards[i];
        return Card(
          elevation: 2,
          child: InkWell(
            onTap: () => showModalBottomSheet<void>(
              context: context,
              useSafeArea: true,
              showDragHandle: true,
              isScrollControlled: true,
              builder: (_) => HazardDetailSheet(report: r),
            ),
            child: ListTile(
              leading: Icon(_iconFor(r.type), color: _colorFor(r.severity)),
              title: Text(r.advisoryType ?? r.type.label),
              subtitle: Text('${r.location}\n${r.timestamp.toLocal()}'),
              isThreeLine: true,
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (r.distanceKm != null) _distanceBadge(context, r.distanceKm!),
                  const SizedBox(height: 6),
                  const Icon(Icons.chevron_right),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _distanceBadge(BuildContext context, double km) {
    final Color color = _distanceColor(km);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        '${km.toStringAsFixed(1)} km',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }

  Color _distanceColor(double km) {
    if (km <= 1.0) return Colors.red;
    if (km <= 3.0) return Colors.orange;
    if (km <= 5.0) return Colors.amber.shade800;
    return Colors.grey;
  }

  IconData _iconFor(HazardType type) {
    switch (type) {
      case HazardType.landslide:
        return Icons.terrain_rounded;
      case HazardType.flood:
        return Icons.water_damage_rounded;
      case HazardType.roadblock:
        return Icons.block_rounded;
      case HazardType.snowfall:
        return Icons.ac_unit_rounded;
      case HazardType.protest:
        return Icons.groups_2_rounded;
      case HazardType.accident:
        return Icons.local_hospital_rounded;
    }
  }

  Color _colorFor(Severity severity) {
    switch (severity) {
      case Severity.low:
        return Colors.green;
      case Severity.medium:
        return Colors.orange;
      case Severity.high:
      case Severity.critical:
        return Colors.red;
    }
  }
}

