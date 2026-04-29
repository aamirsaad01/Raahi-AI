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
  bool _hasCurrentItinerary = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final user = await AuthSession.load();
      if (user == null) {
        if (!mounted) return;
        setState(() {
          _hasCurrentItinerary = false;
          _conversations = <ChatConversation>[];
        });
        return;
      }
      final Map<String, dynamic> resume = await _api.getActiveSession(user.userId);
      final int? anchor = resume['linked_itinerary_id'] != null
          ? (resume['linked_itinerary_id'] as num).toInt()
          : null;
      final bool hasAnchor = anchor != null;
      final List<ChatConversation> all = await _api.getSessions(user.userId);
      final List<ChatConversation> filtered = anchor == null
          ? <ChatConversation>[]
          : all
              .where(
                (ChatConversation c) => c.linkedItineraryId == anchor,
              )
              .toList();
      if (!mounted) return;
      setState(() {
        _hasCurrentItinerary = hasAnchor;
        _conversations = filtered;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _hasCurrentItinerary = false;
        _conversations = <ChatConversation>[];
      });
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
          : _conversations.isEmpty
              ? ListView(
                  padding: const EdgeInsets.all(24).add(AppConstants.footerPadding),
                  children: <Widget>[
                    Text(
                      _hasCurrentItinerary
                          ? 'No chat history for your current trip yet.'
                          : 'No itinerary yet',
                      style: Theme.of(context).textTheme.bodyLarge,
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _hasCurrentItinerary
                          ? 'Open AI Chat and send a message to start. Only the chat for your latest itinerary appears here.'
                          : 'Generate an itinerary first. Chat history is shown per trip.',
                      style: Theme.of(context).textTheme.bodySmall,
                      textAlign: TextAlign.center,
                    ),
                  ],
                )
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
                        subtitle: Text(_formatTime(conv.lastMessageTime)),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {
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

