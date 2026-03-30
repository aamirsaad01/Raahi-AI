import 'package:flutter/material.dart';
import 'models.dart';
import '../../utils/app_constants.dart';

class CostBreakdownPage extends StatelessWidget {
  final TripItinerary itinerary;
  const CostBreakdownPage({super.key, required this.itinerary});

  @override
  Widget build(BuildContext context) {
    final cost = itinerary.costBreakdown;
    if (cost == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Cost Breakdown')),
        body: const Center(child: Text('No cost breakdown available')),
      );
    }
    
    final TextTheme text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Cost Breakdown')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0).add(AppConstants.footerPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _Row('Total Budget', cost.totalBudget, text),
            _Row('Total Estimated', cost.totalEstimated, text),
            _Row('Remaining', cost.remaining, text, isRemaining: true),
            const Divider(height: 32),
            Text('Breakdown', style: text.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            _Row('Attractions', cost.breakdown.attractions, text),
            _Row('Accommodation', cost.breakdown.accommodation, text),
            _Row('Food', cost.breakdown.food, text),
            _Row('Transport', cost.breakdown.transport, text),
            if (cost.perDay != null) ...[
              const Divider(height: 32),
              Text('Per Day', style: text.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              _Row('Accommodation (per night)', cost.perDay!.accommodation, text),
              _Row('Food (per day)', cost.perDay!.food, text),
            ],
          ],
        ),
      ),
    );
  }

  Widget _Row(String label, double value, TextTheme text, {bool isTotal = false, bool isRemaining = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Text(label, style: isTotal ? text.titleMedium : text.bodyLarge),
          Text(
            'PKR ${value.toStringAsFixed(2)}',
            style: (isTotal || isRemaining)
                ? text.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: isRemaining ? (value >= 0 ? Colors.green : Colors.red) : null,
                    )
                : text.bodyLarge,
          ),
        ],
      ),
    );
  }
}


