import 'package:flutter/material.dart';
import 'models.dart';
import '../../utils/app_constants.dart';

class PoiDetailPage extends StatelessWidget {
  final TimeSlot slot;
  const PoiDetailPage({super.key, required this.slot});

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final colors = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: Text(slot.locationName)),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16).add(AppConstants.footerScrollInsets(context)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Time and type
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                Chip(label: Text(slot.timeOfDay)),
                Chip(label: Text('${slot.startTime} – ${slot.endTime}')),
                Chip(label: Text(slot.activityType)),
              ],
            ),
            const SizedBox(height: 16),
            if (slot.estimatedCostPkr != '0' && slot.estimatedCostPkr.isNotEmpty) ...[
              Row(
                children: [
                  Icon(Icons.payments_outlined, size: 20, color: colors.primary),
                  const SizedBox(width: 8),
                  Text('PKR ${slot.estimatedCostPkr}',
                      style: text.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 16),
            ],
            if (slot.description.isNotEmpty) ...[
              Text(slot.description, style: text.bodyLarge?.copyWith(height: 1.6)),
              const SizedBox(height: 16),
            ],
            if (slot.travelTips.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.amber.shade50,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.amber.shade200),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.lightbulb_outline,
                        size: 20, color: Colors.amber.shade800),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Travel Tips',
                              style: text.titleSmall?.copyWith(
                                color: Colors.amber.shade900,
                                fontWeight: FontWeight.bold,
                              )),
                          const SizedBox(height: 4),
                          Text(slot.travelTips,
                              style: text.bodyMedium?.copyWith(
                                color: Colors.amber.shade900,
                                height: 1.5,
                              )),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
