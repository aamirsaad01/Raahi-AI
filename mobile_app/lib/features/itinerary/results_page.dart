import 'package:flutter/material.dart';
import 'models.dart';
import 'api_service.dart';
import '../auth/auth_session.dart';
import '../emergency/emergency_contact_service.dart';
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
  final EmergencyContactService _emergencyContactService = EmergencyContactService();
  final TextEditingController _emergencyNameCtrl = TextEditingController();
  final TextEditingController _emergencyRelationCtrl = TextEditingController();
  final TextEditingController _emergencyPhoneCtrl = TextEditingController();
  TripItinerary? _itinerary;
  bool _isLoading = true;
  String? _error;
  bool _savingEmergencyContact = false;
  bool _pendingEmergencyContactSave = false;
  String? _emergencySaveStatus;

  @override
  void dispose() {
    _emergencyNameCtrl.dispose();
    _emergencyRelationCtrl.dispose();
    _emergencyPhoneCtrl.dispose();
    super.dispose();
  }

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
      if (widget.form.destination == null || widget.form.destination!.isEmpty) {
        setState(() {
          _error = 'No destination selected. Please go back and select a destination.';
          _isLoading = false;
        });
        return;
      }

      final mood = _apiService.moodToBackend(widget.form.mood);
      final sessionUser = await AuthSession.load();

      final itinerary = await _apiService.generateItinerary(
        userId: sessionUser?.userId,
        destination: widget.form.destination!,
        days: widget.form.durationDays,
        budget: widget.form.budget,
        mood: mood,
        activities: widget.form.activities,
        travelMonth: widget.form.travelMonth,
        numPeople: widget.form.numPeople,
        corridorId: widget.form.corridorId,
      );

      setState(() {
        _itinerary = itinerary;
        _isLoading = false;
      });
      if (_pendingEmergencyContactSave) {
        await _saveEmergencyContactNow(showSuccessSnack: true);
      }
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
        body: SingleChildScrollView(
          padding: EdgeInsets.all(16).add(AppConstants.footerScrollInsets(context)),
          child: Column(
            children: [
              const SizedBox(height: 10),
              const CircularProgressIndicator(),
              const SizedBox(height: 18),
              Text(
                'Generating itinerary in background...',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 6),
              Text(
                'While we prepare your trip, add one emergency contact.',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
              ),
              const SizedBox(height: 18),
              _EmergencyContactFormCard(
                nameController: _emergencyNameCtrl,
                relationController: _emergencyRelationCtrl,
                phoneController: _emergencyPhoneCtrl,
                isSaving: _savingEmergencyContact,
                status: _emergencySaveStatus,
                onSave: () async {
                  if (_itinerary == null) {
                    setState(() {
                      _pendingEmergencyContactSave = true;
                      _emergencySaveStatus =
                          'Contact noted. It will be linked once itinerary is ready.';
                    });
                    return;
                  }
                  await _saveEmergencyContactNow(showSuccessSnack: true);
                },
              ),
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
        title: Text(itin.title, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          if (itin.locationInfo != null)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: _IconFilledButton(
                icon: Icons.map_rounded,
                tooltip: 'Route Map',
                onTap: () => Navigator.of(context)
                    .pushNamed(AppRoutes.itineraryMap, arguments: itin),
              ),
            ),
        ],
      ),
      body: ListView(
        padding: EdgeInsets.all(16).add(AppConstants.footerScrollInsets(context)),
        children: [
          _OverviewHeader(itinerary: itin),
          const SizedBox(height: 20),
          if (itin.packingRecommendations.isNotEmpty) ...[
            _PackingSection(items: itin.packingRecommendations),
            const SizedBox(height: 20),
          ],
          Text(
            'Day-by-Day Plan',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 12),
          ...itin.daysPlan.map((day) => _DayTimelineCard(day: day)),
        ],
      ),
    );
  }

  Future<void> _saveEmergencyContactNow({required bool showSuccessSnack}) async {
    final itin = _itinerary;
    if (itin == null) return;
    final name = _emergencyNameCtrl.text.trim();
    final relation = _emergencyRelationCtrl.text.trim();
    final phone = _emergencyPhoneCtrl.text.trim();
    if (name.length < 2 || relation.length < 2 || phone.length < 10) {
      setState(() {
        _emergencySaveStatus = 'Please enter valid emergency contact details.';
      });
      return;
    }

    setState(() => _savingEmergencyContact = true);
    try {
      await _emergencyContactService.saveForItinerary(
        itineraryId: int.tryParse(itin.id) ?? 0,
        contactName: name,
        relationship: relation,
        phoneNumber: phone,
      );
      if (!mounted) return;
      setState(() {
        _pendingEmergencyContactSave = false;
        _emergencySaveStatus = 'Emergency contact linked with this itinerary.';
      });
      if (showSuccessSnack) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Emergency contact saved.')),
        );
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _emergencySaveStatus = e.toString().replaceAll('Exception: ', '');
      });
    } finally {
      if (mounted) setState(() => _savingEmergencyContact = false);
    }
  }
}

class _EmergencyContactFormCard extends StatelessWidget {
  final TextEditingController nameController;
  final TextEditingController relationController;
  final TextEditingController phoneController;
  final bool isSaving;
  final String? status;
  final Future<void> Function() onSave;

  const _EmergencyContactFormCard({
    required this.nameController,
    required this.relationController,
    required this.phoneController,
    required this.isSaving,
    required this.status,
    required this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Emergency Contact',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: nameController,
              decoration: const InputDecoration(
                labelText: 'Name of emergency contact',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: relationController,
              decoration: const InputDecoration(
                labelText: "Person's relationship with emergency contact",
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: phoneController,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Phone number of emergency contact',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: isSaving ? null : onSave,
                icon: const Icon(Icons.save_outlined),
                label: Text(isSaving ? 'Saving...' : 'Save Emergency Contact'),
              ),
            ),
            if (status != null && status!.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                status!,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Overview header with trip narrative, cost range, and hazard banner
// ---------------------------------------------------------------------------

class _OverviewHeader extends StatelessWidget {
  final TripItinerary itinerary;
  const _OverviewHeader({required this.itinerary});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final cost = itinerary.estimatedCostRange;

    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              itinerary.title,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.place, size: 18, color: colors.primary),
                const SizedBox(width: 6),
                Text('${itinerary.destination}, ${itinerary.region}'),
                const Spacer(),
                Icon(Icons.calendar_today, size: 18, color: colors.primary),
                const SizedBox(width: 6),
                Text('${itinerary.days} Days'),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.people, size: 18, color: colors.primary),
                const SizedBox(width: 6),
                Text('${itinerary.numPeople} ${itinerary.numPeople == 1 ? "Person" : "People"}'),
                const Spacer(),
                Icon(Icons.account_balance_wallet, size: 18, color: colors.primary),
                const SizedBox(width: 6),
                Text('PKR ${_fmt(cost.min)} – ${_fmt(cost.max)}'),
              ],
            ),
            if (itinerary.estimatedTransportCostPkr != null &&
                itinerary.estimatedTransportCostPkr! > 0) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.directions_car_outlined, size: 18,
                      color: colors.onSurfaceVariant),
                  const SizedBox(width: 6),
                  Text(
                    'Transport: ~PKR ${_fmt(itinerary.estimatedTransportCostPkr!)}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: colors.onSurfaceVariant,
                        ),
                  ),
                ],
              ),
            ],
            if (itinerary.locationInfo != null) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.wb_sunny_outlined, size: 18,
                      color: colors.onSurfaceVariant),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      [
                        itinerary.locationInfo!.climateZone,
                        itinerary.locationInfo!.touristSeason,
                      ].where((s) => s != null && s.isNotEmpty).join(' · '),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ],
            if (itinerary.tripOverview.isNotEmpty) ...[
              const Divider(height: 24),
              Text(
                itinerary.tripOverview,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      height: 1.5,
                    ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  static String _fmt(int v) {
    if (v >= 1000) {
      return '${(v / 1000).toStringAsFixed(v % 1000 == 0 ? 0 : 1)}k';
    }
    return v.toString();
  }
}

// ---------------------------------------------------------------------------
// Packing recommendations
// ---------------------------------------------------------------------------

class _PackingSection extends StatelessWidget {
  final List<String> items;
  const _PackingSection({required this.items});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.tertiaryContainer.withOpacity(0.4),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.backpack_outlined,
                    color: Theme.of(context).colorScheme.tertiary),
                const SizedBox(width: 8),
                Text(
                  'Packing Recommendations',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...items.map((item) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('• ', style: TextStyle(fontWeight: FontWeight.bold)),
                      Expanded(child: Text(item)),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Day card with vertical timeline
// ---------------------------------------------------------------------------

class _DayTimelineCard extends StatelessWidget {
  final DayPlan day;
  const _DayTimelineCard({required this.day});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      child: InkWell(
        onTap: () => Navigator.of(context)
            .pushNamed(AppRoutes.itineraryDay, arguments: day),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Day header
              Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: colors.primaryContainer,
                      borderRadius: BorderRadius.circular(22),
                    ),
                    child: Center(
                      child: Text(
                        '${day.dayNumber}',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: colors.onPrimaryContainer,
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
                          day.themeTitle,
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        if (day.daySummary.isNotEmpty)
                          Text(
                            day.daySummary,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: colors.onSurfaceVariant,
                                ),
                          ),
                      ],
                    ),
                  ),
                  Icon(Icons.chevron_right, color: colors.onSurfaceVariant),
                ],
              ),
              if (day.timeSlots.isNotEmpty) ...[
                const SizedBox(height: 12),
                // Mini timeline preview (max 3 slots)
                ...day.timeSlots.take(3).toList().asMap().entries.map((entry) {
                  final idx = entry.key;
                  final slot = entry.value;
                  final isLast = idx == (day.timeSlots.length > 3
                      ? 2
                      : day.timeSlots.length - 1);

                  return _MiniTimelineItem(
                    slot: slot,
                    isLast: isLast,
                  );
                }),
                if (day.timeSlots.length > 3)
                  Padding(
                    padding: const EdgeInsets.only(left: 28, top: 4),
                    child: Text(
                      '+${day.timeSlots.length - 3} more activities',
                      style: Theme.of(context).textTheme.labelMedium?.copyWith(
                            color: colors.primary,
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                  ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _MiniTimelineItem extends StatelessWidget {
  final TimeSlot slot;
  final bool isLast;
  const _MiniTimelineItem({required this.slot, required this.isLast});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final dotColor = _dotColor(slot.timeOfDay, colors);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline rail
          SizedBox(
            width: 28,
            child: Column(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    color: dotColor,
                    shape: BoxShape.circle,
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: colors.outlineVariant,
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Row(
                children: [
                  SizedBox(
                    width: 72,
                    child: Text(
                      slot.startTime,
                      style: Theme.of(context)
                          .textTheme
                          .labelSmall
                          ?.copyWith(color: colors.onSurfaceVariant),
                    ),
                  ),
                  Icon(
                    _activityIcon(slot.activityType),
                    size: 16,
                    color: colors.onSurfaceVariant,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      slot.displayTitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
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
// Reusable icon button
// ---------------------------------------------------------------------------

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
