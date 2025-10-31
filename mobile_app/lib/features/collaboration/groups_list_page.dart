import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';

class GroupsListPage extends StatelessWidget {
  const GroupsListPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<TripGroup> groups = <TripGroup>[
      TripGroup(
        id: 'g1',
        name: 'Hunza Trip 2024',
        startDate: DateTime.now().add(const Duration(days: 5)),
        endDate: DateTime.now().add(const Duration(days: 12)),
        members: const <GroupMember>[],
      ),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Collaboration Suite')),
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 60),
        child: FloatingActionButton.extended(
          onPressed: () => Navigator.of(context).pushNamed(AppRoutes.collaborationCreate),
          icon: const Icon(Icons.add_rounded),
          label: const Text('Create Group'),
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(12),
        itemCount: groups.length + 1,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (BuildContext context, int i) {
          if (i == groups.length) {
            return Card(
              child: ListTile(
                leading: const Icon(Icons.group_add_rounded),
                title: const Text('Join Group'),
                subtitle: const Text('Enter invite code'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).pushNamed(AppRoutes.collaborationJoin),
              ),
            );
          }
          final TripGroup g = groups[i];
          return Card(
            child: ListTile(
              leading: const Icon(Icons.group_rounded),
              title: Text(g.name),
              subtitle: Text('${g.members.length} members • ${g.startDate} - ${g.endDate}'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.collaborationChat, arguments: g),
            ),
          );
        },
      ),
    );
  }
}

