import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';

class AiChatHistoryPage extends StatelessWidget {
  const AiChatHistoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    final List<ChatConversation> conversations = <ChatConversation>[
      ChatConversation(
        id: 'c1',
        title: 'Hunza travel route',
        lastMessageTime: DateTime.now().subtract(const Duration(hours: 2)),
        messageCount: 8,
      ),
      ChatConversation(
        id: 'c2',
        title: 'Weather forecast',
        lastMessageTime: DateTime.now().subtract(const Duration(days: 1)),
        messageCount: 5,
      ),
      ChatConversation(
        id: 'c3',
        title: 'Best places to visit',
        lastMessageTime: DateTime.now().subtract(const Duration(days: 3)),
        messageCount: 12,
      ),
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Chat History')),
      body: ListView.separated(
        padding: const EdgeInsets.all(12),
        itemCount: conversations.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (BuildContext context, int i) {
          final ChatConversation conv = conversations[i];
          return Card(
            child: ListTile(
              leading: const Icon(Icons.chat_bubble_outline_rounded),
              title: Text(conv.title),
              subtitle: Text('${conv.messageCount} messages • ${_formatTime(conv.lastMessageTime)}'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () {
                // Could navigate back to chat with this conversation loaded
                Navigator.of(context).pop();
              },
            ),
          );
        },
      ),
    );
  }

  String _formatTime(DateTime time) {
    final Duration diff = DateTime.now().difference(time);
    if (diff.inDays > 0) return '${diff.inDays} days ago';
    if (diff.inHours > 0) return '${diff.inHours} hours ago';
    if (diff.inMinutes > 0) return '${diff.inMinutes} minutes ago';
    return 'Just now';
  }
}

