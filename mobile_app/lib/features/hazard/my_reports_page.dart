import 'package:flutter/material.dart';
import 'models.dart';

class MyReportsPage extends StatelessWidget {
  const MyReportsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<HazardReport> mine = <HazardReport>[
      HazardReport(
        id: 'me1',
        type: HazardType.roadblock,
        severity: Severity.medium,
        timestamp: DateTime.now().subtract(const Duration(hours: 2)),
        source: 'You',
        lat: 33.6938,
        lon: 73.0652,
        location: 'Islamabad',
        description: 'Road construction causing delays.',
      ),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('My Reports')),
      body: ListView.separated(
        itemCount: mine.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (BuildContext context, int i) {
          final HazardReport r = mine[i];
          return ListTile(
            leading: Icon(Icons.flag_rounded, color: Colors.orange.shade700),
            title: Text(r.type.label),
            subtitle: Text('${r.location} (${r.lat.toStringAsFixed(4)}, ${r.lon.toStringAsFixed(4)}) • ${r.timestamp}'),
          );
        },
      ),
    );
  }
}


