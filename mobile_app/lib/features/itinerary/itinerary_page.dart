import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';
import '../../widgets/app_footer_nav.dart';

class ItineraryFormPage extends StatefulWidget {
  const ItineraryFormPage({super.key});

  @override
  State<ItineraryFormPage> createState() => _ItineraryFormPageState();
}

class _ItineraryFormPageState extends State<ItineraryFormPage> {
  Mood _mood = Mood.adventurous;
  final TextEditingController _budget = TextEditingController();
  String _season = 'Summer';
  final Set<String> _activities = <String>{};
  int _duration = 6;

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
        padding: const EdgeInsets.all(16),
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
            _Section('Season', child: DropdownButtonFormField<String>(
              value: _season,
              items: const <DropdownMenuItem<String>>[
                DropdownMenuItem<String>(value: 'Summer', child: Text('Summer')),
                DropdownMenuItem<String>(value: 'Winter', child: Text('Winter')),
                DropdownMenuItem<String>(value: 'Spring', child: Text('Spring')),
                DropdownMenuItem<String>(value: 'Autumn', child: Text('Autumn')),
              ],
              onChanged: (String? v) => setState(() => _season = v ?? 'Summer'),
            )),
            const SizedBox(height: 12),
            _Section('Activities', child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: <String>['Hiking', 'Camping', 'Photography', 'Food', 'City Tour']
                  .map((String a) => FilterChip(
                        label: Text(a),
                        selected: _activities.contains(a),
                        onSelected: (bool s) => setState(() => s ? _activities.add(a) : _activities.remove(a)),
                      ))
                  .toList(),
            )),
            const SizedBox(height: 12),
            _Section('Duration (days)', child: Row(
              children: <Widget>[
                IconButton(onPressed: _duration > 1 ? () => setState(() => _duration--) : null, icon: const Icon(Icons.remove_circle_outline)),
                Text('$_duration'),
                IconButton(onPressed: () => setState(() => _duration++), icon: const Icon(Icons.add_circle_outline)),
              ],
            )),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _budget.text.trim().isEmpty ? null : () {
                  final ItineraryFormData data = ItineraryFormData(
                    mood: _mood,
                    budget: int.tryParse(_budget.text.trim()) ?? 0,
                    season: _season,
                    activities: _activities.toList(),
                    durationDays: _duration,
                  );
                  Navigator.of(context).pushNamed(AppRoutes.itineraryResults, arguments: data);
                },
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Generate Itinerary'),
              ),
            ),
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


