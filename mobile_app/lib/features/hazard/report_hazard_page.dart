import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'models.dart';
import '../../utils/app_constants.dart';
import 'api_service.dart';

class ReportHazardPage extends StatefulWidget {
  const ReportHazardPage({super.key});

  @override
  State<ReportHazardPage> createState() => _ReportHazardPageState();
}

class _ReportHazardPageState extends State<ReportHazardPage> {
  final HazardApiService _apiService = HazardApiService();
  HazardType _type = HazardType.roadblock;
  Severity _severity = Severity.medium;
  final TextEditingController _title = TextEditingController();
  final TextEditingController _desc = TextEditingController();
  final TextEditingController _location = TextEditingController();
  final TextEditingController _lat = TextEditingController();
  final TextEditingController _lon = TextEditingController();
  bool _isSubmitting = false;
  bool _isGeocoding = false;
  bool _fetchingCoords = false;

  @override
  void dispose() {
    _title.dispose();
    _desc.dispose();
    _location.dispose();
    _lat.dispose();
    _lon.dispose();
    super.dispose();
  }

  Future<void> _fetchCurrentCoordinates() async {
    setState(() => _fetchingCoords = true);
    try {
      final enabled = await Geolocator.isLocationServiceEnabled();
      if (!enabled) {
        throw Exception('Location services are turned off.');
      }
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        throw Exception('Location permission denied.');
      }
      Position pos;
      try {
        pos = await Geolocator.getCurrentPosition(
          locationSettings: const LocationSettings(
            accuracy: LocationAccuracy.high,
          ),
        ).timeout(const Duration(seconds: 12));
      } catch (_) {
        final last = await Geolocator.getLastKnownPosition();
        if (last != null) {
          pos = last;
        } else {
          rethrow;
        }
      }
      if (!mounted) return;
      setState(() {
        _lat.text = pos.latitude.toStringAsFixed(6);
        _lon.text = pos.longitude.toStringAsFixed(6);
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Coordinates filled from your current location.')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not get location: $e'), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _fetchingCoords = false);
    }
  }

  double? _parseOptionalCoord(String s) {
    final t = s.trim();
    if (t.isEmpty) return null;
    return double.tryParse(t.replaceAll(',', '.'));
  }

  Future<void> _submitHazard() async {
    if (_title.text.trim().isEmpty || _location.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill all required fields')),
      );
      return;
    }

    final double? lat = _parseOptionalCoord(_lat.text);
    final double? lon = _parseOptionalCoord(_lon.text);
    if ((lat != null) != (lon != null)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Enter both latitude and longitude, or leave both empty to use the location name.'),
        ),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
      _isGeocoding = lat == null && lon == null;
    });

    try {
      await _apiService.reportHazard(
        type: _type,
        severity: _severity,
        location: _location.text.trim(),
        title: _title.text.trim(),
        description: _desc.text.trim().isEmpty ? null : _desc.text.trim(),
        latitude: lat,
        longitude: lon,
      );

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Hazard reported successfully!'),
          backgroundColor: Colors.green,
        ),
      );

      Navigator.of(context).pop(true); // Return true to indicate success
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 4),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
          _isGeocoding = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report Hazard')),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16.0).add(AppConstants.footerScrollInsets(context)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            TextField(
              controller: _title,
              decoration: const InputDecoration(
                labelText: 'Title *',
                hintText: 'e.g., Road Block on Karakoram Highway',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<HazardType>(
              value: _type,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Hazard Type *'),
              items: HazardType.values
                  .map((HazardType t) => DropdownMenuItem<HazardType>(value: t, child: Text(t.label)))
                  .toList(),
              onChanged: (HazardType? v) => setState(() => _type = v ?? _type),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<Severity>(
              value: _severity,
              decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Severity *'),
              items: Severity.values
                  .map((Severity s) => DropdownMenuItem<Severity>(value: s, child: Text(s.label)))
                  .toList(),
              onChanged: (Severity? v) => setState(() => _severity = v ?? _severity),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _location,
              decoration: const InputDecoration(
                labelText: 'Location Name *',
                hintText: 'e.g., Murree, Naran, Gilgit, Karakoram Highway',
                border: OutlineInputBorder(),
                helperText: 'If latitude/longitude below are empty, coordinates are resolved from this name',
              ),
            ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Expanded(
                  child: TextField(
                    controller: _lat,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                    decoration: const InputDecoration(
                      labelText: 'Latitude (optional)',
                      hintText: 'e.g., 34.0522',
                      border: OutlineInputBorder(),
                      helperText: 'Decimal degrees',
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _lon,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                    decoration: const InputDecoration(
                      labelText: 'Longitude (optional)',
                      hintText: 'e.g., 73.2167',
                      border: OutlineInputBorder(),
                      helperText: 'Decimal degrees',
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _desc,
              minLines: 3,
              maxLines: 5,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'Description (optional)',
                hintText: 'Additional details about the hazard...',
              ),
            ),
            const SizedBox(height: 24),
            if (_isGeocoding)
              const Padding(
                padding: EdgeInsets.only(bottom: 12.0),
                child: Row(
                  children: [
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    SizedBox(width: 12),
                    Text('Finding location coordinates...'),
                  ],
                ),
              ),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _isSubmitting || _fetchingCoords ? null : _fetchCurrentCoordinates,
                icon: _fetchingCoords
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.my_location_rounded),
                label: Text(_fetchingCoords ? 'Getting location...' : 'Fetch Current Coordinates'),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _isSubmitting ? null : _submitHazard,
                icon: _isSubmitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.send_rounded),
                label: Text(_isSubmitting ? 'Submitting...' : 'Submit Report'),
              ),
            )
          ],
        ),
      ),
    );
  }
}


