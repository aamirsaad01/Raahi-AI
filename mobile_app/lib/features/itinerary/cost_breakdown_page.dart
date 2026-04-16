import 'package:flutter/material.dart';
import 'models.dart';
import '../../utils/app_constants.dart';

class CostBreakdownPage extends StatelessWidget {
  final TripItinerary itinerary;
  const CostBreakdownPage({super.key, required this.itinerary});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final colors = Theme.of(context).colorScheme;
    final cost = itinerary.estimatedCostRange;

    return Scaffold(
      appBar: AppBar(title: const Text('Cost Breakdown')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16).add(AppConstants.footerPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              color: colors.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Estimated Total Cost',
                        style: text.titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(
                      'PKR ${cost.min.toStringAsFixed(0)} – ${cost.max.toStringAsFixed(0)}',
                      style: text.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: colors.onPrimaryContainer,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'For ${itinerary.numPeople} ${itinerary.numPeople == 1 ? "person" : "people"} · ${itinerary.days} days',
                      style: text.bodyMedium?.copyWith(
                        color: colors.onPrimaryContainer.withOpacity(0.7),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Budget: PKR ${itinerary.totalBudget.toStringAsFixed(0)}',
                      style: text.titleSmall,
                    ),
                    const SizedBox(height: 4),
                    LinearProgressIndicator(
                      value: itinerary.totalBudget > 0
                          ? (cost.max / itinerary.totalBudget).clamp(0.0, 1.0)
                          : 0,
                      backgroundColor: colors.onPrimaryContainer.withOpacity(0.15),
                      color: cost.max <= itinerary.totalBudget
                          ? Colors.green
                          : Colors.red,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text('Per-Day Activity Costs',
                style: text.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            ...itinerary.daysPlan.map((day) {
              int dayTotal = 0;
              for (final slot in day.timeSlots) {
                dayTotal += int.tryParse(slot.estimatedCostPkr) ?? 0;
              }
              return ListTile(
                leading: CircleAvatar(
                  child: Text('${day.dayNumber}'),
                ),
                title: Text(day.themeTitle),
                subtitle: Text('${day.timeSlots.length} activities'),
                trailing: Text(
                  'PKR $dayTotal',
                  style: text.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
