import 'package:flutter/material.dart';

class LayersFiltersSheet extends StatefulWidget {
  const LayersFiltersSheet({super.key});

  @override
  State<LayersFiltersSheet> createState() => _LayersFiltersSheetState();
}

class _LayersFiltersSheetState extends State<LayersFiltersSheet> {
  bool ndma = true;
  bool pmd = true;
  bool user = true;
  int timeWindow = 0; // 0: 24h, 1: 7d, 2: 1m, 3: all

  static const List<String> _timeOptions = [
    'Last 24 hours', 'Last 7 days', 'Last 1 month', 'All Time'
  ];

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text('Layers & Filters', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: <Widget>[
              FilterChip(label: const Text('NDMA'), selected: ndma, onSelected: (bool s) => setState(() => ndma = s)),
              FilterChip(label: const Text('PMD'), selected: pmd, onSelected: (bool s) => setState(() => pmd = s)),
              FilterChip(label: const Text('User Reports'), selected: user, onSelected: (bool s) => setState(() => user = s)),
            ],
          ),
          const SizedBox(height: 16),
          const Text('Time Window'),
          Wrap(
            spacing: 8,
            children: List<Widget>.generate(_timeOptions.length, (int i) => ChoiceChip(
                label: Text(_timeOptions[i]),
                selected: timeWindow == i,
                onSelected: (bool s) => setState(() { if (s) timeWindow = i; }),
              )
            ),
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: FilledButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Apply')),
          )
        ],
      ),
    );
  }
}


