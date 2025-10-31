import 'package:flutter/material.dart';

class EmergencySettingsPage extends StatefulWidget {
  const EmergencySettingsPage({super.key});

  @override
  State<EmergencySettingsPage> createState() => _EmergencySettingsPageState();
}

class _EmergencySettingsPageState extends State<EmergencySettingsPage> {
  bool autoSwitch = true;
  bool prefetchTiles = true;
  bool includeHazards = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Emergency Settings')),
      body: ListView(
        children: <Widget>[
          SwitchListTile(
            value: autoSwitch,
            onChanged: (bool v) => setState(() => autoSwitch = v),
            title: const Text('Auto-switch to Emergency Mode'),
            subtitle: const Text('Based on connectivity, battery and movement'),
          ),
          SwitchListTile(
            value: prefetchTiles,
            onChanged: (bool v) => setState(() => prefetchTiles = v),
            title: const Text('Prefetch offline map tiles'),
          ),
          SwitchListTile(
            value: includeHazards,
            onChanged: (bool v) => setState(() => includeHazards = v),
            title: const Text('Include latest hazards in prefetch'),
          ),
        ],
      ),
    );
  }
}


