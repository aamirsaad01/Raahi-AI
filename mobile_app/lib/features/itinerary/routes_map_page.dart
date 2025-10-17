import 'package:flutter/material.dart';
import 'models.dart';
import '../../widgets/app_footer_nav.dart';

class RoutesMapPage extends StatelessWidget {
  final TripItinerary itinerary;
  const RoutesMapPage({super.key, required this.itinerary});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Route Map')),
      body: const Center(child: Text('Map placeholder (Mapbox/OSM later).')),
    );
  }
}


