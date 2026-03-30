import 'package:flutter/material.dart';

class LayersFiltersSheet extends StatefulWidget {
  final String? initialSource;
  final String initialTimeWindow;
  final String? initialSeverity;
  final Function(String?, String?, String)? onApply;

  const LayersFiltersSheet({
    super.key,
    this.initialSource,
    this.initialTimeWindow = 'all',
    this.initialSeverity,
    this.onApply,
  });

  @override
  State<LayersFiltersSheet> createState() => _LayersFiltersSheetState();
}

class _LayersFiltersSheetState extends State<LayersFiltersSheet> {
  late bool ndma;
  late bool pmd;
  late bool user;
  late int timeWindow;
  String? severityFilter;

  static const List<String> _timeOptions = [
    'Last 24 hours', 'Last 7 days', 'Last 1 month', 'All Time'
  ];
  
  static const List<String> _timeValues = ['24h', '7d', '1m', 'all'];

  @override
  void initState() {
    super.initState();
    // Initialize from widget parameters
    ndma = widget.initialSource == null || widget.initialSource == 'ndma';
    pmd = widget.initialSource == null || widget.initialSource == 'pmd';
    user = widget.initialSource == null || widget.initialSource == 'user';
    
    // Map time window to index
    final timeIndex = _timeValues.indexOf(widget.initialTimeWindow);
    timeWindow = timeIndex >= 0 ? timeIndex : 3;
    
    severityFilter = widget.initialSeverity;
  }

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
          const Text('Severity'),
          Wrap(
            spacing: 8,
            children: <Widget>[
              ChoiceChip(
                label: const Text('All'),
                selected: severityFilter == null,
                onSelected: (bool s) => setState(() { if (s) severityFilter = null; }),
              ),
              ChoiceChip(
                label: const Text('Low'),
                selected: severityFilter == 'low',
                onSelected: (bool s) => setState(() { if (s) severityFilter = 'low'; }),
              ),
              ChoiceChip(
                label: const Text('Medium'),
                selected: severityFilter == 'medium',
                onSelected: (bool s) => setState(() { if (s) severityFilter = 'medium'; }),
              ),
              ChoiceChip(
                label: const Text('High'),
                selected: severityFilter == 'high',
                onSelected: (bool s) => setState(() { if (s) severityFilter = 'high'; }),
              ),
              ChoiceChip(
                label: const Text('Critical'),
                selected: severityFilter == 'critical',
                onSelected: (bool s) => setState(() { if (s) severityFilter = 'critical'; }),
              ),
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
            child: FilledButton(
              onPressed: () {
                // Determine source filter
                String? source;
                if (ndma && !pmd && !user) {
                  source = 'ndma';
                } else if (!ndma && pmd && !user) {
                  source = 'pmd';
                } else if (!ndma && !pmd && user) {
                  source = 'user';
                } else if (!ndma && !pmd && !user) {
                  source = 'none'; // Show nothing
                } else {
                  source = null; // Show all
                }
                
                final timeValue = _timeValues[timeWindow];
                
                if (widget.onApply != null) {
                  widget.onApply!(source, severityFilter, timeValue);
                }
                Navigator.of(context).pop();
              },
              child: const Text('Apply'),
            ),
          )
        ],
      ),
    );
  }
}


