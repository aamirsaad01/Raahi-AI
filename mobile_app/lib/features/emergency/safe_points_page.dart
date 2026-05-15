import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../utils/app_constants.dart';
import 'nearby_safe_points_page.dart';
import 'safe_points_api_service.dart';

class SafePointsPage extends StatefulWidget {
  const SafePointsPage({super.key});

  @override
  State<SafePointsPage> createState() => _SafePointsPageState();
}

class _SafePointsPageState extends State<SafePointsPage> {
  final SafePointsApiService _service = SafePointsApiService();
  bool _loadingCities = true;
  bool _loadingPoints = false;
  String? _error;
  List<String> _cities = <String>[];
  String? _selectedCity;
  List<SafePoint> _points = <SafePoint>[];

  @override
  void initState() {
    super.initState();
    _loadCities();
  }

  Future<void> _loadCities() async {
    setState(() {
      _loadingCities = true;
      _error = null;
    });
    try {
      final List<String> cities = await _service.fetchCities();
      if (!mounted) return;
      setState(() {
        _cities = cities;
        _selectedCity = cities.isNotEmpty ? cities.first : null;
      });
      if (_selectedCity != null) {
        await _loadSafePointsForCity(_selectedCity!);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loadingCities = false);
    }
  }

  Future<void> _loadSafePointsForCity(String city) async {
    setState(() {
      _loadingPoints = true;
      _error = null;
    });
    try {
      final List<SafePoint> points = await _service.fetchByCity(city);
      if (!mounted) return;
      setState(() => _points = points);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loadingPoints = false);
    }
  }

  IconData _categoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'hospital':
        return Icons.local_hospital_rounded;
      case 'police station':
        return Icons.local_police_rounded;
      case 'fuel station':
        return Icons.local_gas_station_rounded;
      case 'car workshop':
        return Icons.car_repair_rounded;
      default:
        return Icons.place_rounded;
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Safe Points')),
      body: _loadingCities
          ? const Center(child: CircularProgressIndicator())
          : _error != null && _cities.isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    Text('Failed to load cities.\n$_error'),
                    const SizedBox(height: 12),
                    FilledButton(
                      onPressed: _loadCities,
                      child: const Text('Try Again'),
                    ),
                  ],
                ),
              ),
            )
          : RefreshIndicator(
              onRefresh: () async {
                if (_selectedCity == null) return;
                await _loadSafePointsForCity(_selectedCity!);
              },
              child: ListView(
                padding: EdgeInsets.all(16).add(AppConstants.footerScrollInsets(context)),
                children: <Widget>[
                      DropdownButtonFormField<String>(
                        initialValue: _selectedCity,
                    decoration: const InputDecoration(
                      labelText: 'Select City',
                      border: OutlineInputBorder(),
                    ),
                    items: _cities
                        .map(
                          (String city) => DropdownMenuItem<String>(
                            value: city,
                            child: Text(city),
                          ),
                        )
                        .toList(),
                    onChanged: (String? value) {
                      if (value == null) return;
                      setState(() => _selectedCity = value);
                      _loadSafePointsForCity(value);
                    },
                  ),
                  const SizedBox(height: 12),
                  if (_loadingPoints)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Center(child: CircularProgressIndicator()),
                    )
                  else ...<Widget>[
                    if (_error != null)
                      Card(
                        color: Theme.of(context).colorScheme.errorContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Text(
                            'Could not load safe points: $_error',
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onErrorContainer,
                            ),
                          ),
                        ),
                      ),
                    if (_error != null) const SizedBox(height: 8),
                    Text(
                      _selectedCity == null
                          ? 'No city selected'
                          : '${_points.length} safe points in $_selectedCity',
                    ),
                    const SizedBox(height: 8),
                    if (_points.isEmpty)
                      const Card(
                        child: Padding(
                          padding: EdgeInsets.all(14),
                          child: Text(
                            'No safe points available for this city yet.',
                          ),
                        ),
                      ),
                    ..._points.map((SafePoint p) {
                      return Card(
                        child: ListTile(
                          onTap: () => _openMaps(p),
                          leading: Icon(_categoryIcon(p.category)),
                          title: Text(p.name),
                          subtitle: Text(p.location),
                          trailing: Chip(label: Text(p.category)),
                        ),
                      );
                    }),
                  ],
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => const NearbySafePointsPage(),
                          ),
                        );
                      },
                      icon: const Icon(Icons.near_me_rounded),
                      label: const Text('Fetch Nearby Safe Points'),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
