import 'package:flutter/material.dart';
import 'models.dart';
import '../../routes/app_routes.dart';
import '../../widgets/app_footer_nav.dart';

class ItineraryResultsPage extends StatelessWidget {
  final ItineraryFormData form;
  const ItineraryResultsPage({super.key, required this.form});

  @override
  Widget build(BuildContext context) {
    final TripItinerary itin = _fakeItinerary(form);
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
        padding: const EdgeInsets.all(12),
        children: <Widget>[
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: itin.highlights.map((String h) => Chip(label: Text(h))).toList(),
          ),
          const SizedBox(height: 12),
          ...itin.days.map((DayPlan d) => Card(
                child: ListTile(
                  title: Text('Day ${d.dayNumber}')
                    ,
                  subtitle: Text(d.stops.map((Poi p) => p.name).join(' → ')),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.of(context).pushNamed(AppRoutes.itineraryDay, arguments: d),
                ),
              )),
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

TripItinerary _fakeItinerary(ItineraryFormData form) {
  final List<Poi> poi = <Poi>[
    const Poi(id: '1', name: 'Hunza Valley', region: 'Gilgit-Baltistan', bestSeason: 'Summer', activityType: 'Sightseeing', difficulty: 'Easy'),
    const Poi(id: '2', name: 'Attabad Lake', region: 'Gilgit-Baltistan', bestSeason: 'Summer', activityType: 'Boating', difficulty: 'Easy'),
    const Poi(id: '3', name: 'Khunjerab Pass', region: 'Gilgit-Baltistan', bestSeason: 'Summer', activityType: 'Scenic Drive', difficulty: 'Medium'),
  ];
  final List<DayPlan> days = <DayPlan>[
    DayPlan(dayNumber: 1, stops: <Poi>[poi[0]]),
    DayPlan(dayNumber: 2, stops: <Poi>[poi[1]]),
    DayPlan(dayNumber: 3, stops: <Poi>[poi[2]]),
  ];
  return TripItinerary(
    id: 'demo',
    title: '${form.mood.label} ${form.durationDays}-day Trip',
    days: days,
    estimatedCost: 120000,
    highlights: <String>['Scenic Views', 'Local Cuisine', 'Comfortable Stays'],
  );
}


