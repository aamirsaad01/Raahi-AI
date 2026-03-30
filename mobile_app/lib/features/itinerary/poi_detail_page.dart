import 'package:flutter/material.dart';
import 'models.dart';
import '../../utils/app_constants.dart';

class PoiDetailPage extends StatelessWidget {
  final Poi poi;
  const PoiDetailPage({super.key, required this.poi});

  @override
  Widget build(BuildContext context) {
    final TextTheme text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: Text(poi.name)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0).add(AppConstants.footerPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(poi.region, style: text.titleMedium),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: <Widget>[
                Chip(label: Text('Best: ${poi.bestSeason}')),
                Chip(label: Text('Activity: ${poi.activityType}')),
                Chip(label: Text('Difficulty: ${poi.difficulty}')),
              ],
            ),
            const SizedBox(height: 12),
            if (poi.description != null) Text(poi.description!),
          ],
        ),
      ),
    );
  }
}


