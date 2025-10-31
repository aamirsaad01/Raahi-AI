import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';
import 'hazard_detail_sheet.dart';
import 'layers_filters_sheet.dart';

class HazardMapPage extends StatelessWidget {
  const HazardMapPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<HazardReport> sample = <HazardReport>[
      HazardReport(
        id: 'h1',
        type: HazardType.landslide,
        severity: Severity.high,
        timestamp: DateTime.now().subtract(const Duration(hours: 3)),
        source: 'NDMA',
        lat: 35.9208,
        lon: 74.3089,
        location: 'Karimabad, Hunza',
        description: 'Landslide blocking the road near Karimabad.',
      ),
      HazardReport(
        id: 'h2',
        type: HazardType.flood,
        severity: Severity.medium,
        timestamp: DateTime.now().subtract(const Duration(hours: 8)),
        source: 'PMD',
        lat: 24.8607,
        lon: 67.0011,
        location: 'Karachi',
        description: 'Urban flooding risk due to heavy rainfall.',
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Hazard Map'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.layers_rounded,
              tooltip: 'Layers & Filters',
              onTap: () => showModalBottomSheet<void>(
                context: context,
                useSafeArea: true,
                showDragHandle: true,
                isScrollControlled: true,
                builder: (_) => const LayersFiltersSheet(),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.bookmark_rounded,
              tooltip: 'My Reports',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.hazardMyReports),
            ),
          ),
        ],
      ),
      floatingActionButton: SafeArea(
        minimum: const EdgeInsets.only(bottom: 60),
        child: FloatingActionButton.extended(
          onPressed: () => Navigator.of(context).pushNamed(AppRoutes.hazardReport),
          icon: const Icon(Icons.add_location_alt_rounded),
          label: const Text('Report'),
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(12),
        itemCount: sample.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (BuildContext context, int i) {
          final HazardReport r = sample[i];
          return Card(
            child: ListTile(
              leading: Icon(Icons.location_on_rounded, color: _colorFor(r.severity)),
              title: Text(r.type.label),
              subtitle: Text('${r.location} (${r.lat.toStringAsFixed(4)}, ${r.lon.toStringAsFixed(4)}) • ${r.source} • ${r.timestamp}'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => showModalBottomSheet<void>(
                context: context,
                useSafeArea: true,
                showDragHandle: true,
                builder: (_) => HazardDetailSheet(report: r),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _IconFilledButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final String? tooltip;

  const _IconFilledButton({required this.icon, required this.onTap, this.tooltip});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final Widget btn = Material(
      color: colors.primary,
      shape: const StadiumBorder(),
      child: InkWell(
        customBorder: const StadiumBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Icon(icon, color: Colors.white),
        ),
      ),
    );
    if (tooltip != null) return Tooltip(message: tooltip!, child: btn);
    return btn;
  }
}

Color _colorFor(Severity s) {
  switch (s) {
    case Severity.low:
      return Colors.green;
    case Severity.medium:
      return Colors.orange;
    case Severity.high:
      return Colors.deepOrange;
    case Severity.critical:
      return Colors.red;
  }
}


