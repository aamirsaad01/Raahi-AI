import 'package:flutter/material.dart';
import 'models.dart';

class CollaborationMapPage extends StatelessWidget {
  const CollaborationMapPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Route & Live Locations')),
      body: const Center(
        child: Text('Map with itinerary route and member locations (placeholder).'),
      ),
    );
  }
}

