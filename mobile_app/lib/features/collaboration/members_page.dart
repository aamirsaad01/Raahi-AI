import 'package:flutter/material.dart';
import 'models.dart';

class MembersPage extends StatelessWidget {
  const MembersPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<GroupMember> members = <GroupMember>[
      const GroupMember(id: 'u1', name: 'Ahmed', isOnline: true, lat: 35.9208, lon: 74.3089),
      GroupMember(id: 'u2', name: 'Sara', isOnline: false, lat: 35.9100, lon: 74.3000, lastSeen: DateTime.now()),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Members')),
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 60),
        child: FloatingActionButton.extended(
          onPressed: () {
            // Show dialog to add member by username
            showDialog<void>(
              context: context,
              builder: (BuildContext context) {
                final TextEditingController username = TextEditingController();
                return AlertDialog(
                  title: const Text('Add Member'),
                  content: TextField(
                    controller: username,
                    decoration: const InputDecoration(labelText: 'Username', border: OutlineInputBorder()),
                    autofocus: true,
                  ),
                  actions: <Widget>[
                    TextButton(
                      onPressed: () {
                        username.dispose();
                        Navigator.of(context).pop();
                      },
                      child: const Text('Cancel'),
                    ),
                    FilledButton(
                      onPressed: () {
                        if (username.text.trim().isNotEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Added ${username.text} (stub)')));
                          username.dispose();
                          Navigator.of(context).pop();
                        }
                      },
                      child: const Text('Add'),
                    ),
                  ],
                );
              },
            );
          },
          icon: const Icon(Icons.person_add_rounded),
          label: const Text('Add Member'),
        ),
      ),
      body: ListView.builder(
        itemCount: members.length,
        itemBuilder: (BuildContext context, int i) {
          final GroupMember m = members[i];
          return ListTile(
            leading: CircleAvatar(
              backgroundColor: m.isOnline ? Colors.green : Colors.grey,
              child: Text(m.name[0]),
            ),
            title: Text(m.name),
            subtitle: m.isOnline
                ? Text('Online • ${m.lat?.toStringAsFixed(4)}, ${m.lon?.toStringAsFixed(4)}')
                : Text('Offline • Last seen: ${m.lastSeen}'),
            trailing: const Icon(Icons.location_on_rounded),
          );
        },
      ),
    );
  }
}

