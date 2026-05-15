import 'package:flutter/material.dart';
import 'models.dart';
import '../../utils/app_constants.dart';

class DayDetailPage extends StatelessWidget {
  final DayPlan day;
  const DayDetailPage({super.key, required this.day});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(day.displayHeading),
      ),
      body: ListView(
        padding: EdgeInsets.all(16).add(AppConstants.footerScrollInsets(context)),
        children: [
          if (day.daySummary.isNotEmpty) ...[
            Card(
              color: Theme.of(context)
                  .colorScheme
                  .secondaryContainer
                  .withOpacity(0.4),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline,
                        size: 20,
                        color: Theme.of(context).colorScheme.secondary),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        day.daySummary,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              height: 1.5,
                            ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],
          // Full timeline with transit indicators
          ...day.timeSlots.asMap().entries.expand((entry) {
            final idx = entry.key;
            final slot = entry.value;
            final isLast = idx == day.timeSlots.length - 1;
            return [
              if (idx > 0 && slot.hasTransitInfo)
                _TransitBanner(slot: slot),
              _TimelineSlotCard(slot: slot, isLast: isLast),
            ];
          }),
          if (day.timeSlots.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 40),
                child: Text(
                  'No activities planned for this day',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Detailed timeline slot card (expandable)
// ---------------------------------------------------------------------------

class _TimelineSlotCard extends StatefulWidget {
  final TimeSlot slot;
  final bool isLast;
  const _TimelineSlotCard({required this.slot, required this.isLast});

  @override
  State<_TimelineSlotCard> createState() => _TimelineSlotCardState();
}

class _TimelineSlotCardState extends State<_TimelineSlotCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final slot = widget.slot;
    final dotColor = _dotColor(slot.timeOfDay, colors);

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline dot
          Padding(
            padding: const EdgeInsets.only(top: 18),
            child: Container(
              width: 14,
              height: 14,
              decoration: BoxDecoration(
                color: dotColor,
                shape: BoxShape.circle,
                border: Border.all(color: colors.surface, width: 2),
                boxShadow: [
                  BoxShadow(
                    color: dotColor.withOpacity(0.4),
                    blurRadius: 4,
                    spreadRadius: 1,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Card
          Expanded(
            child: Card(
              elevation: 1,
              margin: EdgeInsets.zero,
              child: InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: () => setState(() => _expanded = !_expanded),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Time badge + activity type
                      Row(
                        children: [
                          _TimeBadge(
                            label: slot.timeOfDay,
                            color: dotColor,
                          ),
                          const SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              '${slot.startTime} – ${slot.endTime}',
                              style: Theme.of(context)
                                  .textTheme
                                  .labelMedium
                                  ?.copyWith(color: colors.onSurfaceVariant),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: colors.surfaceContainerHighest,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  _activityIcon(slot.activityType),
                                  size: 14,
                                  color: colors.onSurface,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  slot.activityType,
                                  style: Theme.of(context)
                                      .textTheme
                                      .labelSmall
                                      ?.copyWith(fontWeight: FontWeight.w600),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      // Activity at Location
                      Text(
                        slot.displayTitle,
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 6),
                      // Cost chip
                      if (slot.estimatedCostPkr != '0' &&
                          slot.estimatedCostPkr.isNotEmpty)
                        Chip(
                          avatar: Icon(Icons.payments_outlined,
                              size: 16, color: colors.primary),
                          label: Text('PKR ${slot.estimatedCostPkr}'),
                          labelStyle:
                              Theme.of(context).textTheme.labelSmall,
                          padding: EdgeInsets.zero,
                          materialTapTargetSize:
                              MaterialTapTargetSize.shrinkWrap,
                        ),
                      // Expandable description + tips + transit
                      AnimatedSize(
                        duration: const Duration(milliseconds: 250),
                        alignment: Alignment.topCenter,
                        child: _expanded
                            ? Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  const SizedBox(height: 10),
                                  Text(
                                    slot.description,
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(height: 1.5),
                                  ),
                                  if (slot.travelTips.isNotEmpty) ...[
                                    const SizedBox(height: 12),
                                    Container(
                                      padding: const EdgeInsets.all(12),
                                      decoration: BoxDecoration(
                                        color: Colors.amber.shade50,
                                        borderRadius:
                                            BorderRadius.circular(8),
                                        border: Border.all(
                                            color:
                                                Colors.amber.shade200),
                                      ),
                                      child: Row(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Icon(Icons.lightbulb_outline,
                                              size: 18,
                                              color:
                                                  Colors.amber.shade800),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Text(
                                              slot.travelTips,
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .bodySmall
                                                  ?.copyWith(
                                                    color: Colors
                                                        .amber.shade900,
                                                    height: 1.4,
                                                  ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                  if (slot.hasTransitInfo) ...[
                                    const SizedBox(height: 12),
                                    _InlineTransitChip(slot: slot),
                                  ],
                                ],
                              )
                            : const SizedBox.shrink(),
                      ),
                      // Expand hint
                      Align(
                        alignment: Alignment.centerRight,
                        child: Icon(
                          _expanded
                              ? Icons.expand_less
                              : Icons.expand_more,
                          size: 20,
                          color: colors.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _dotColor(String timeOfDay, ColorScheme colors) {
    switch (timeOfDay.toLowerCase()) {
      case 'early morning':
        return Colors.orange.shade400;
      case 'morning':
        return Colors.amber.shade700;
      case 'late morning':
        return Colors.amber.shade600;
      case 'afternoon':
        return colors.primary;
      case 'late afternoon':
        return Colors.teal;
      case 'evening':
        return Colors.indigo;
      case 'night':
        return Colors.blueGrey.shade800;
      default:
        return colors.primary;
    }
  }

  static IconData _activityIcon(String activityType) {
    switch (activityType.toLowerCase()) {
      case 'hiking':
        return Icons.hiking;
      case 'breakfast':
      case 'lunch':
      case 'dinner':
      case 'dining':
        return Icons.restaurant;
      case 'photography':
        return Icons.camera_alt_outlined;
      case 'check-in':
      case 'check-out':
      case 'hotel':
        return Icons.hotel_outlined;
      case 'rest':
      case 'free time':
        return Icons.self_improvement;
      case 'scenic drive':
      case 'transit':
      case 'drive':
        return Icons.directions_car_outlined;
      case 'boating':
        return Icons.directions_boat_outlined;
      case 'shopping':
        return Icons.shopping_bag_outlined;
      case 'swimming':
        return Icons.pool_outlined;
      case 'cultural visit':
        return Icons.museum_outlined;
      case 'camping setup':
      case 'camping':
        return Icons.cabin_outlined;
      case 'stargazing':
        return Icons.nights_stay_outlined;
      case 'sightseeing':
        return Icons.visibility_outlined;
      default:
        return Icons.place_outlined;
    }
  }
}

// ---------------------------------------------------------------------------
// Inline transit chip shown inside the expanded card
// ---------------------------------------------------------------------------

class _InlineTransitChip extends StatelessWidget {
  final TimeSlot slot;
  const _InlineTransitChip({required this.slot});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final mins = slot.transitFromPreviousMins ?? 0;
    final km = slot.transitDistanceKm;
    final instruction = slot.transitInstruction ?? '';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: colors.primaryContainer.withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: colors.primaryContainer),
      ),
      child: Row(
        children: [
          Icon(Icons.directions_car_outlined,
              size: 16, color: colors.primary),
          const SizedBox(width: 8),
          Expanded(
            child: Text.rich(
              TextSpan(
                children: [
                  TextSpan(
                    text: [
                      '$mins min',
                      if (km != null) '${km.toStringAsFixed(1)} km',
                    ].join(' · '),
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: colors.primary,
                        ),
                  ),
                  if (instruction.isNotEmpty)
                    TextSpan(
                      text: '  $instruction',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: colors.onSurfaceVariant,
                          ),
                    ),
                ],
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Transit banner between time slots
// ---------------------------------------------------------------------------

class _TransitBanner extends StatelessWidget {
  final TimeSlot slot;
  const _TransitBanner({required this.slot});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final mins = slot.transitFromPreviousMins ?? 0;
    final km = slot.transitDistanceKm;
    final instruction = slot.transitInstruction ?? '';

    return Padding(
      padding: const EdgeInsets.only(left: 36, bottom: 4),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: colors.primaryContainer.withOpacity(0.25),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: colors.primaryContainer),
        ),
        child: Row(
          children: [
            Icon(Icons.directions_car_outlined,
                size: 18, color: colors.primary),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    [
                      '$mins min drive',
                      if (km != null) '${km.toStringAsFixed(1)} km',
                    ].join(' · '),
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: colors.primary,
                        ),
                  ),
                  if (instruction.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Text(
                      instruction,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: colors.onSurfaceVariant,
                            height: 1.3,
                          ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Small badge widget
// ---------------------------------------------------------------------------

class _TimeBadge extends StatelessWidget {
  final String label;
  final Color color;
  const _TimeBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }
}
