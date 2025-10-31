import 'package:flutter/material.dart';

class SafePointsPage extends StatelessWidget {
  const SafePointsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<Map<String, String>> pois = <Map<String, String>>[
      <String, String>{'name': 'DHQ Hospital', 'distance': '1.2 km'},
      <String, String>{'name': 'Police Station', 'distance': '2.0 km'},
      <String, String>{'name': 'Fuel Station', 'distance': '2.5 km'},
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Safe Points')),
      body: ListView.builder(
        itemCount: pois.length,
        itemBuilder: (BuildContext context, int i) {
          final Map<String, String> p = pois[i];
          return ListTile(
            leading: const Icon(Icons.place_rounded),
            title: Text(p['name']!),
            subtitle: Text(p['distance']!),
            trailing: FilledButton(
              onPressed: () {},
              child: const Text('Route'),
            ),
          );
        },
      ),
    );
  }
}


