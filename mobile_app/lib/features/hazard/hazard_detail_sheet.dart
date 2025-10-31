import 'package:flutter/material.dart';
import 'models.dart';

class HazardDetailSheet extends StatelessWidget {
  final HazardReport report;
  const HazardDetailSheet({super.key, required this.report});

  @override
  Widget build(BuildContext context) {
    final TextTheme text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(_iconFor(report.type), color: _colorFor(report.severity)),
              const SizedBox(width: 12),
              Text(report.type.label, style: text.titleMedium),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _colorFor(report.severity).withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(report.severity.label),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text('${report.location} (${report.lat.toStringAsFixed(4)}, ${report.lon.toStringAsFixed(4)})'),
          const SizedBox(height: 4),
          Text('Source: ${report.source}'),
          Text('Time: ${report.timestamp}'),
          const SizedBox(height: 8),
          if (report.description != null) Text(report.description!),
          const SizedBox(height: 8),
          Row(
            children: <Widget>[
              const Spacer(),
              TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Close')),
            ],
          )
        ],
      ),
    );
  }

  IconData _iconFor(HazardType t) {
    switch (t) {
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
}


