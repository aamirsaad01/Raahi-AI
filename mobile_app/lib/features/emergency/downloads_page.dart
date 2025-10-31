import 'package:flutter/material.dart';

class EmergencyDownloadsPage extends StatelessWidget {
  const EmergencyDownloadsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Offline Downloads')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: <Widget>[
          _Tile(title: 'Northern Region Tiles', progress: 0.7),
          _Tile(title: 'Safe Points POIs', progress: 1.0),
          _Tile(title: 'Latest Hazard Data', progress: 0.35),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.download_rounded),
            label: const Text('Download Selected'),
          ),
        ],
      ),
    );
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


