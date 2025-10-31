import 'package:flutter/material.dart';

class EmergencyOutboxPage extends StatelessWidget {
  const EmergencyOutboxPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<Map<String, String>> queue = <Map<String, String>>[
      <String, String>{'to': '+92 300 1234567', 'status': 'Queued'},
      <String, String>{'to': '1122', 'status': 'Queued'},
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Queued Messages')),
      body: ListView.separated(
        itemCount: queue.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (BuildContext context, int i) {
          final Map<String, String> m = queue[i];
          return ListTile(
            leading: const Icon(Icons.schedule_send_rounded),
            title: Text('To: ${m['to']}'),
            subtitle: Text(m['status']!),
            trailing: IconButton(onPressed: () {}, icon: const Icon(Icons.cancel_outlined)),
          );
        },
      ),
    );
  }
}


