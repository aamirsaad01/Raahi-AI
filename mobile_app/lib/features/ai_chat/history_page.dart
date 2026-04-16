import 'package:flutter/material.dart';
import '../../utils/app_constants.dart';
import '../auth/auth_session.dart';
import 'api_service.dart';
import 'models.dart';

class AiChatHistoryPage extends StatefulWidget {
  const AiChatHistoryPage({super.key});

  @override
  State<AiChatHistoryPage> createState() => _AiChatHistoryPageState();
}

class _AiChatHistoryPageState extends State<AiChatHistoryPage> {
  final AiChatApiService _api = AiChatApiService();
  bool _loading = true;
  List<ChatConversation> _conversations = <ChatConversation>[];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final user = await AuthSession.load();
      if (user != null) {
        final conv = await _api.getSessions(user.userId);
        if (!mounted) return;
        setState(() => _conversations = conv);
      }
    } catch (_) {
      if (!mounted) return;
      setState(() => _conversations = <ChatConversation>[]);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chat History')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView.separated(
        padding: const EdgeInsets.all(12).add(AppConstants.footerPadding),
        itemCount: _conversations.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (BuildContext context, int i) {
          final ChatConversation conv = _conversations[i];
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

