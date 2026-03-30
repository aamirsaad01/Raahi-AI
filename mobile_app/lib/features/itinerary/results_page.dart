import 'package:flutter/material.dart';
import 'models.dart';
import 'api_service.dart';
import '../../routes/app_routes.dart';
import '../../utils/app_constants.dart';

class ItineraryResultsPage extends StatefulWidget {
  final ItineraryFormData form;
  const ItineraryResultsPage({super.key, required this.form});

  @override
  State<ItineraryResultsPage> createState() => _ItineraryResultsPageState();
}

class _ItineraryResultsPageState extends State<ItineraryResultsPage> {
  final ItineraryApiService _apiService = ItineraryApiService();
  TripItinerary? _itinerary;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _generateItinerary();
  }

  Future<void> _generateItinerary() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Ensure destination is selected
      if (widget.form.destination == null || widget.form.destination!.isEmpty) {
        setState(() {
          _error = 'No destination selected. Please go back and select a destination.';
          _isLoading = false;
        });
        return;
      }

      // Convert form data to API format
      final mood = _apiService.moodToBackend(widget.form.mood);
      
      final itinerary = await _apiService.generateItinerary(
        // userId is optional - not required for anonymous users
        destination: widget.form.destination!,
        days: widget.form.durationDays,
        budget: widget.form.budget,
        mood: mood,
        activities: widget.form.activities,
        travelMonth: widget.form.travelMonth,
        numPeople: widget.form.numPeople,
      );

      setState(() {
        _itinerary = itinerary;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString().replaceAll('Exception: ', '');
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Generating Itinerary')),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Creating your perfect itinerary...'),
            ],
          ),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 64, color: Colors.red),
                const SizedBox(height: 16),
                Text(
                  'Failed to generate itinerary',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  _error!,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _generateItinerary,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Try Again'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (_itinerary == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: const Center(child: Text('No itinerary data')),
      );
    }

    final itin = _itinerary!;
    return Scaffold(
      appBar: AppBar(
        title: Text(itin.title),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.payments_outlined,
              tooltip: 'Cost Breakdown',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.itineraryCost, arguments: itin),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.map_rounded,
              tooltip: 'Route Map',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.itineraryMap, arguments: itin),
            ),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16).add(AppConstants.footerPadding),
        children: <Widget>[
          // General Information Section
          _GeneralInfoSection(itinerary: itin),
          const SizedBox(height: 24),
          
          // Cost Breakdown Section
          if (itin.costBreakdown != null) ...[
            _CostBreakdownSection(costBreakdown: itin.costBreakdown!),
            const SizedBox(height: 24),
          ],
          
          // Daily Plan Section
          Text(
            'Daily Plan',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          ...itin.daysPlan.asMap().entries.map((entry) {
            final day = entry.value;
            return _DayCard(day: day, dayIndex: entry.key);
          }),
        ],
      ),
    );
  }
}

class _GeneralInfoSection extends StatelessWidget {
  final TripItinerary itinerary;

  const _GeneralInfoSection({required this.itinerary});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              itinerary.title,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.place, size: 20, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        itinerary.destination,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(
                        itinerary.region,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.calendar_today, size: 20, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  '${itinerary.days} ${itinerary.days == 1 ? 'Day' : 'Days'}',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
                const SizedBox(width: 24),
                Icon(Icons.account_balance_wallet, size: 20, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'PKR ${itinerary.totalBudget.toStringAsFixed(0)}',
                  style: Theme.of(context).textTheme.bodyLarge,
                ),
              ],
            ),
            if (itinerary.locationInfo != null) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.info_outline, size: 20, color: Theme.of(context).colorScheme.onSurfaceVariant),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${itinerary.locationInfo!.climateZone ?? 'N/A'} • ${itinerary.locationInfo!.touristSeason ?? 'N/A'}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CostBreakdownSection extends StatelessWidget {
  final CostBreakdown costBreakdown;

  const _CostBreakdownSection({required this.costBreakdown});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Cost Breakdown',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Icon(
                  Icons.account_balance_wallet,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ],
            ),
            const SizedBox(height: 16),
            _CostRow(
              label: 'Total Budget',
              amount: costBreakdown.totalBudget,
              isTotal: false,
            ),
            _CostRow(
              label: 'Total Estimated',
              amount: costBreakdown.totalEstimated,
              isTotal: false,
            ),
            _CostRow(
              label: 'Remaining',
              amount: costBreakdown.remaining,
              isTotal: false,
              isRemaining: true,
            ),
            const Divider(height: 24),
            Text(
              'Breakdown',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            _CostRow(
              label: 'Attractions',
              amount: costBreakdown.breakdown.attractions,
              isTotal: false,
            ),
            _CostRow(
              label: 'Accommodation',
              amount: costBreakdown.breakdown.accommodation,
              isTotal: false,
            ),
            _CostRow(
              label: 'Food',
              amount: costBreakdown.breakdown.food,
              isTotal: false,
            ),
            _CostRow(
              label: 'Transport',
              amount: costBreakdown.breakdown.transport,
              isTotal: false,
            ),
            if (costBreakdown.perDay != null) ...[
              const Divider(height: 24),
              Text(
                'Per Day',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              _CostRow(
                label: 'Accommodation (per night)',
                amount: costBreakdown.perDay!.accommodation,
                isTotal: false,
              ),
              _CostRow(
                label: 'Food (per day)',
                amount: costBreakdown.perDay!.food,
                isTotal: false,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CostRow extends StatelessWidget {
  final String label;
  final double amount;
  final bool isTotal;
  final bool isRemaining;

  const _CostRow({
    required this.label,
    required this.amount,
    this.isTotal = false,
    this.isRemaining = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: isTotal
                ? Theme.of(context).textTheme.titleMedium
                : Theme.of(context).textTheme.bodyMedium,
          ),
          Text(
            'PKR ${amount.toStringAsFixed(2)}',
            style: (isTotal || isRemaining)
                ? Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: isRemaining
                          ? (amount >= 0 ? Colors.green : Colors.red)
                          : null,
                    )
                : Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

class _DayCard extends StatelessWidget {
  final DayPlan day;
  final int dayIndex;

  const _DayCard({required this.day, required this.dayIndex});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      child: InkWell(
        onTap: () => Navigator.of(context).pushNamed(AppRoutes.itineraryDay, arguments: day),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: Center(
                      child: Text(
                        '${day.dayNumber}',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).colorScheme.onPrimaryContainer,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Day ${day.dayNumber}',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (day.date != null)
                          Text(
                            day.date!,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).colorScheme.onSurfaceVariant,
                            ),
                          ),
                      ],
                    ),
                  ),
                  if (day.totalDurationHours != null)
                    Chip(
                      label: Text('${day.totalDurationHours!.toStringAsFixed(1)}h'),
                      avatar: const Icon(Icons.access_time, size: 16),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              if (day.stops.isNotEmpty) ...[
                Text(
                  'Places to Visit',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                ...day.stops.map((poi) => _PoiItem(poi: poi)),
              ] else
                Text(
                  'No stops planned for this day',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              if (day.estimatedCost != null) ...[
                const SizedBox(height: 12),
                const Divider(),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Day Cost',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    Text(
                      'PKR ${day.estimatedCost!.toStringAsFixed(2)}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _PoiItem extends StatelessWidget {
  final Poi poi;

  const _PoiItem({required this.poi});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  poi.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              if (poi.rating != null) ...[
                Icon(Icons.star, size: 16, color: Colors.amber),
                const SizedBox(width: 4),
                Text(
                  poi.rating!.toStringAsFixed(1),
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ],
          ),
          if (poi.time != null) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.access_time, size: 14, color: Theme.of(context).colorScheme.onSurfaceVariant),
                const SizedBox(width: 4),
                Text(
                  poi.time!,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (poi.durationHours != null) ...[
                  const SizedBox(width: 8),
                  Text(
                    '• ${poi.durationHours!.toStringAsFixed(1)} hours',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ],
            ),
          ],
          if (poi.description != null && poi.description!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              poi.description!,
              style: Theme.of(context).textTheme.bodySmall,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              if (poi.activityType.isNotEmpty)
                Chip(
                  label: Text(poi.activityType),
                  labelStyle: Theme.of(context).textTheme.labelSmall,
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              if (poi.difficulty.isNotEmpty)
                Chip(
                  label: Text(poi.difficulty),
                  labelStyle: Theme.of(context).textTheme.labelSmall,
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              if (poi.cost != null && poi.cost! > 0)
                Chip(
                  label: Text('PKR ${poi.cost!.toStringAsFixed(0)}'),
                  labelStyle: Theme.of(context).textTheme.labelSmall,
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
            ],
          ),
          if (poi.highlights.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: poi.highlights.take(3).map((highlight) {
                return Chip(
                  label: Text(highlight),
                  labelStyle: Theme.of(context).textTheme.labelSmall,
                  padding: EdgeInsets.zero,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }
}

class _IconFilledButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final String? tooltip;

  const _IconFilledButton({required this.icon, required this.onTap, this.tooltip});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final Widget btn = Material(
      color: colors.primary,
      shape: const StadiumBorder(),
      child: InkWell(
        customBorder: const StadiumBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Icon(icon, color: Colors.white),
        ),
      ),
    );
    if (tooltip != null) {
      return Tooltip(message: tooltip!, child: btn);
    }
    return btn;
  }
}
