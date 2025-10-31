import 'package:flutter/material.dart';
import 'models.dart';
import '../../widgets/app_footer_nav.dart';

class CostBreakdownPage extends StatelessWidget {
  final TripItinerary itinerary;
  const CostBreakdownPage({super.key, required this.itinerary});

  @override
  Widget build(BuildContext context) {
    final CostBreakdown cost = const CostBreakdown(transport: 40000, stay: 50000, food: 20000, activities: 10000);
    final TextTheme text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Cost Breakdown')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _Row('Transport', cost.transport, text),
            _Row('Stay', cost.stay, text),
            _Row('Food', cost.food, text),
            _Row('Activities', cost.activities, text),
            const Divider(height: 32),
            _Row('Total', cost.total, text, isTotal: true),
          ],
        ),
      ),
    );
  }

  Widget _Row(String label, int value, TextTheme text, {bool isTotal = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Text(label, style: isTotal ? text.titleMedium : text.bodyLarge),
          Text('PKR $value', style: isTotal ? text.titleMedium : text.bodyLarge),
        ],
      ),
    );
  }
}


