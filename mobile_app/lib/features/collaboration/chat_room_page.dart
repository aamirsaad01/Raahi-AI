import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';

class ChatRoomPage extends StatelessWidget {
  final TripGroup group;
  const ChatRoomPage({super.key, required this.group});

  void _showCreatePollDialog(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (BuildContext context) => const _CreatePollDialog(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final List<ChatMessage> messages = <ChatMessage>[
      ChatMessage(
        id: 'm1',
        senderId: 'system',
        senderName: 'System',
        text: 'Weather: Sunny, 25°C. Sunrise: 6:00 AM. Suggested: Early morning hike.',
        timestamp: DateTime.now(),
        type: 'weather',
      ),
      ChatMessage(
        id: 'm2',
        senderId: 'u1',
        senderName: 'Ahmed',
        text: 'Great suggestion! Let\'s meet at 6:30.',
        timestamp: DateTime.now(),
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(group.name),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.people_rounded,
              tooltip: 'Members',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.collaborationMembers),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.map_rounded,
              tooltip: 'Map',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.collaborationMap),
            ),
          ),
        ],
      ),
      body: Column(
        children: <Widget>[
          if (DateTime.now().isAfter(group.endDate))
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.orange.shade100,
              child: const Text('This group will auto-delete soon.'),
            ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: messages.length,
              itemBuilder: (BuildContext context, int i) {
                final ChatMessage m = messages[i];
                if (m.type == 'weather' || m.type == 'summary') {
                  return Card(
                    color: Colors.blue.shade50,
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          Text(m.type == 'weather' ? 'Weather Update' : 'Day Summary', style: Theme.of(context).textTheme.titleSmall),
                          const SizedBox(height: 4),
                          Text(m.text),
                        ],
                      ),
                    ),
                  );
                }
                return ListTile(
                  leading: CircleAvatar(child: Text(m.senderName[0])),
                  title: Text(m.senderName),
                  subtitle: Text(m.text),
                );
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
              margin: const EdgeInsets.only(bottom: 8),
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: TextField(
                      decoration: const InputDecoration(
                        hintText: 'Type a message...',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                    ),
                  ),
                  IconButton(
                    onPressed: () => _showCreatePollDialog(context),
                    icon: const Icon(Icons.poll_rounded),
                    tooltip: 'Create Poll',
                  ),
                  IconButton(onPressed: () {}, icon: const Icon(Icons.send_rounded)),
                ],
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(color: Theme.of(context).colorScheme.surfaceVariant),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: <Widget>[
            TextButton.icon(
              onPressed: () => Navigator.of(context).pushNamed(AppRoutes.collaborationExpenses),
              icon: const Icon(Icons.payments_rounded),
              label: const Text('Expenses'),
            ),
            TextButton.icon(
              onPressed: () => Navigator.of(context).pushNamed(AppRoutes.collaborationPhotos),
              icon: const Icon(Icons.photo_library_rounded),
              label: const Text('Photos'),
            ),
            TextButton.icon(
              onPressed: () => Navigator.of(context).pushNamed(AppRoutes.collaborationPolls),
              icon: const Icon(Icons.poll_rounded),
              label: const Text('Polls'),
            ),
          ],
        ),
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
    if (tooltip != null) return Tooltip(message: tooltip!, child: btn);
    return btn;
  }
}

class _CreatePollDialog extends StatefulWidget {
  const _CreatePollDialog();

  @override
  State<_CreatePollDialog> createState() => _CreatePollDialogState();
}

class _CreatePollDialogState extends State<_CreatePollDialog> {
  final TextEditingController _question = TextEditingController();
  final List<TextEditingController> _options = <TextEditingController>[
    TextEditingController(),
    TextEditingController(),
  ];

  @override
  void dispose() {
    _question.dispose();
    for (final TextEditingController c in _options) c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text('Create Poll', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              TextField(
                controller: _question,
                decoration: const InputDecoration(
                  labelText: 'Question',
                  border: OutlineInputBorder(),
                ),
                autofocus: true,
              ),
              const SizedBox(height: 12),
              ..._options.asMap().entries.map((MapEntry<int, TextEditingController> e) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    children: <Widget>[
                      Expanded(
                        child: TextField(
                          controller: e.value,
                          decoration: InputDecoration(
                            labelText: 'Option ${e.key + 1}',
                            border: const OutlineInputBorder(),
                          ),
                        ),
                      ),
                      if (_options.length > 2)
                        IconButton(
                          onPressed: () {
                            setState(() {
                              _options.removeAt(e.key).dispose();
                            });
                          },
                          icon: const Icon(Icons.remove_circle_outline),
                        ),
                    ],
                  ),
                );
              }),
              TextButton.icon(
                onPressed: () {
                  setState(() => _options.add(TextEditingController()));
                },
                icon: const Icon(Icons.add_rounded),
                label: const Text('Add Option'),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: <Widget>[
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Cancel'),
                  ),
                  const SizedBox(width: 8),
                  FilledButton.icon(
                    onPressed: () {
                      if (_question.text.trim().isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please enter a question')));
                        return;
                      }
                      if (_options.length < 2 || _options.any((TextEditingController c) => c.text.trim().isEmpty)) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please fill all options')));
                        return;
                      }
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Poll created (stub)')));
                      Navigator.of(context).pop();
                    },
                    icon: const Icon(Icons.poll_rounded),
                    label: const Text('Create'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

