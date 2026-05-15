import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import '../../utils/app_constants.dart';
import 'models.dart';

class ItineraryFormPage extends StatefulWidget {
  const ItineraryFormPage({super.key});

  @override
  State<ItineraryFormPage> createState() => _ItineraryFormPageState();
}

class _ItineraryFormPageState extends State<ItineraryFormPage> {
  Mood _mood = Mood.adventurous;
  final TextEditingController _budget = TextEditingController();
  int _travelMonth = 7; // Default to July (Summer)
  final Set<String> _activities = <String>{};
  int _duration = 1;
  int _numPeople = 1;

  String _getSeasonFromMonth(int month) {
    if (month >= 3 && month <= 5) return 'Spring';
    if (month >= 6 && month <= 8) return 'Summer';
    if (month >= 9 && month <= 11) return 'Autumn';
    return 'Winter';
  }

  @override
  void dispose() {
    _budget.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mood-to-Itinerary')),
      body: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(16, 16, 16, 16).add(AppConstants.footerScrollInsets(context)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _Section('Mood', child: Wrap(
              spacing: 8,
              children: Mood.values.map((Mood m) => ChoiceChip(
                label: Text(m.label),
                selected: _mood == m,
                onSelected: (_) => setState(() => _mood = m),
              )).toList(),
            )),
            const SizedBox(height: 12),
            _Section('Budget (PKR)', child: TextField(
              controller: _budget,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(border: OutlineInputBorder(), hintText: 'e.g., 120000'),
            )),
            const SizedBox(height: 12),
            _Section('Travel Month', child: DropdownButtonFormField<int>(
              value: _travelMonth,
              items: const <DropdownMenuItem<int>>[
                DropdownMenuItem<int>(value: 1, child: Text('January')),
                DropdownMenuItem<int>(value: 2, child: Text('February')),
                DropdownMenuItem<int>(value: 3, child: Text('March')),
                DropdownMenuItem<int>(value: 4, child: Text('April')),
                DropdownMenuItem<int>(value: 5, child: Text('May')),
                DropdownMenuItem<int>(value: 6, child: Text('June')),
                DropdownMenuItem<int>(value: 7, child: Text('July')),
                DropdownMenuItem<int>(value: 8, child: Text('August')),
                DropdownMenuItem<int>(value: 9, child: Text('September')),
                DropdownMenuItem<int>(value: 10, child: Text('October')),
                DropdownMenuItem<int>(value: 11, child: Text('November')),
                DropdownMenuItem<int>(value: 12, child: Text('December')),
              ],
              onChanged: (int? v) => setState(() => _travelMonth = v ?? 7),
            )),
            const SizedBox(height: 12),
            _Section('Activities', child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <String>['hiking', 'camping', 'photography', 'food', 'city tour', 'boating', 'sightseeing', 'trekking']
                  .map((String a) => FilterChip(
                        label: Text(a[0].toUpperCase() + a.substring(1)), // Capitalize for display
                        selected: _activities.contains(a),
                        onSelected: (bool s) => setState(() => s ? _activities.add(a) : _activities.remove(a)),
                      ))
                  .toList(),
            )),
            const SizedBox(height: 12),
            _Section('Duration (days)', child: Row(
              children: <Widget>[
                IconButton(onPressed: _duration > 1 ? () => setState(() => _duration--) : null, icon: const Icon(Icons.remove_circle_outline)),
                Text('$_duration', style: Theme.of(context).textTheme.titleLarge),
                IconButton(onPressed: () => setState(() => _duration++), icon: const Icon(Icons.add_circle_outline)),
              ],
            )),
            const SizedBox(height: 12),
            _Section('Number of People', child: Row(
              children: <Widget>[
                IconButton(onPressed: _numPeople > 1 ? () => setState(() => _numPeople--) : null, icon: const Icon(Icons.remove_circle_outline)),
                Text('$_numPeople', style: Theme.of(context).textTheme.titleLarge),
                IconButton(onPressed: () => setState(() => _numPeople++), icon: const Icon(Icons.add_circle_outline)),
              ],
            )),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50, // Fixed height for better visibility
              child: FilledButton.icon(
                style: FilledButton.styleFrom(
                  elevation: 0,
                  shadowColor: Colors.transparent,
                  surfaceTintColor: Colors.transparent,
                ),
                onPressed: _budget.text.trim().isEmpty ? null : () {
                  final budgetValue = int.tryParse(_budget.text.trim());
                  if (budgetValue == null || budgetValue <= 0) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Please enter a valid budget amount')),
                    );
                    return;
                  }
                  
                  final ItineraryFormData data = ItineraryFormData(
                    mood: _mood,
                    budget: budgetValue,
                    season: _getSeasonFromMonth(_travelMonth), // Convert month to season for backward compatibility
                    activities: _activities.toList(),
                    durationDays: _duration,
                    travelMonth: _travelMonth,
                    numPeople: _numPeople,
                  );
                  Navigator.of(context).pushNamed(AppRoutes.itineraryDestinationSelection, arguments: data);
                },
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Get Recommendations'),
              ),
            ),
            const SizedBox(height: 20), // Extra space at bottom
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final Widget child;
  const _Section(this.title, {required this.child});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(title, style: Theme.of(context).textTheme.titleMedium),
        ),
        child,
      ],
    );
  }
}


