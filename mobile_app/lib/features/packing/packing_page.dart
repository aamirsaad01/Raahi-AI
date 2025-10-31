import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';
import '../../widgets/app_footer_nav.dart';

class PackingFormPage extends StatefulWidget {
  const PackingFormPage({super.key});

  @override
  State<PackingFormPage> createState() => _PackingFormPageState();
}

class _PackingFormPageState extends State<PackingFormPage> {
  Region? _region;
  int? _month; // 1-12
  final Set<Activity> _activities = <Activity>{};
  TravelerProfile _profile = TravelerProfile.standard;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final ColorScheme colors = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Packing Checklist'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.bookmark_rounded,
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.packingSaved),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _SectionTitle('Region'),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: Region.values
                  .map((Region r) => ChoiceChip(
                        label: Text(r.label),
                        selected: _region == r,
                        onSelected: (_) => setState(() => _region = r),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 16),
            _SectionTitle('Month'),
            DropdownButtonFormField<int>(
              value: _month,
              decoration: const InputDecoration(border: OutlineInputBorder()),
              items: List<DropdownMenuItem<int>>.generate(12, (int i) {
                final int m = i + 1;
                return DropdownMenuItem<int>(
                  value: m,
                  child: Text(monthName(m)),
                );
              }),
              onChanged: (int? v) => setState(() => _month = v),
            ),
            const SizedBox(height: 16),
            _SectionTitle('Activities'),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: Activity.values
                  .map((Activity a) => FilterChip(
                        label: Text(a.label),
                        selected: _activities.contains(a),
                        onSelected: (bool s) => setState(() {
                          if (s) {
                            _activities.add(a);
                          } else {
                            _activities.remove(a);
                          }
                        }),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 16),
            _SectionTitle('Traveler Profile'),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: TravelerProfile.values
                  .map((TravelerProfile p) => ChoiceChip(
                        label: Text(p.label),
                        selected: _profile == p,
                        onSelected: (_) => setState(() => _profile = p),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _canContinue
                    ? () {
                        Navigator.of(context).pushNamed(
                          AppRoutes.packingResults,
                          arguments: PackingFormData(
                            region: _region!,
                            month: _month!,
                            activities: _activities.toList(),
                            profile: _profile,
                          ),
                        );
                      }
                    : null,
                icon: const Icon(Icons.arrow_forward_rounded),
                label: const Text('Generate Checklist'),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Based on region, month, activities, and traveler needs',
              style: theme.textTheme.bodySmall?.copyWith(color: colors.onSurfaceVariant),
            ),
          ],
        ),
      ),
    );
  }

  bool get _canContinue => _region != null && _month != null;
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(text, style: Theme.of(context).textTheme.titleMedium),
    );
  }
}

class _IconFilledButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _IconFilledButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    return Material(
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
  }
}



