import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import '../../utils/app_constants.dart';
import '../auth/auth_session.dart';
import 'models.dart';
import 'api_service.dart';

class AiChatPage extends StatefulWidget {
  const AiChatPage({super.key});

  @override
  State<AiChatPage> createState() => _AiChatPageState();
}

class _AiChatPageState extends State<AiChatPage> {
  final TextEditingController _messageController = TextEditingController();
  final AiChatApiService _api = AiChatApiService();
  final List<AiChatMessage> _messages = <AiChatMessage>[];
  int? _sessionId;
  int? _userId;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final user = await AuthSession.load();
    if (!mounted) return;
    if (user == null) {
      setState(() {
        _messages.add(
          AiChatMessage(
            id: 'auth_req',
            isUser: false,
            text: 'Please login first to use chatbot.',
            timestamp: DateTime.now(),
            language: ChatLanguage.english,
          ),
        );
      });
      return;
    }
    _userId = user.userId;
    setState(() {
      _messages.add(
        AiChatMessage(
          id: 'welcome',
          isUser: false,
          text:
              'Assalam-o-Alaikum! I can answer with your itinerary, profile and hazards context.',
          timestamp: DateTime.now(),
          language: ChatLanguage.romanUrdu,
        ),
      );
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage() async {
    if (_messageController.text.trim().isEmpty || _sending) return;
    if (_userId == null) return;
    final text = _messageController.text.trim();

    setState(() {
      _sending = true;
      _messages.add(AiChatMessage(
        id: 'user_${DateTime.now().millisecondsSinceEpoch}',
        isUser: true,
        text: text,
        timestamp: DateTime.now(),
      ));
    });
    _messageController.clear();
    try {
      final result = await _api.sendMessage(
        userId: _userId!,
        message: text,
        sessionId: _sessionId,
      );
      if (!mounted) return;
      setState(() {
        _sessionId = (result['session_id'] as num?)?.toInt() ?? _sessionId;
        _messages.add(AiChatMessage(
          id: 'ai_${DateTime.now().millisecondsSinceEpoch}',
          isUser: false,
          text: (result['reply'] ?? '').toString(),
          timestamp: DateTime.now(),
          language: ChatLanguage.romanUrdu,
        ));
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add(AiChatMessage(
          id: 'ai_err_${DateTime.now().millisecondsSinceEpoch}',
          isUser: false,
          text: e.toString().replaceFirst('Exception: ', ''),
          timestamp: DateTime.now(),
          language: ChatLanguage.english,
        ));
      });
    } finally {
      if (mounted) {
        setState(() => _sending = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Chat (Urdu)'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.history_rounded,
              tooltip: 'Chat History',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.aiChatHistory),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: _IconFilledButton(
              icon: Icons.settings_rounded,
              tooltip: 'Settings',
              onTap: () => Navigator.of(context).pushNamed(AppRoutes.aiChatSettings),
            ),
          ),
        ],
      ),
      body: Column(
        children: <Widget>[
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12).add(AppConstants.footerPadding),
              itemCount: _messages.length,
              itemBuilder: (BuildContext context, int index) {
                final AiChatMessage message = _messages[index];
                return _MessageBubble(message: message);
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
              margin: const EdgeInsets.only(bottom: 60),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
              ),
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      decoration: const InputDecoration(
                        hintText: 'Sawal poochhein... (Ask in Urdu/Roman Urdu/English)',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      maxLines: null,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  IconButton(
                    onPressed: _sending ? null : _sendMessage,
                    icon: const Icon(Icons.send_rounded),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final AiChatMessage message;

  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final ColorScheme colors = Theme.of(context).colorScheme;
    final bool isUser = message.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: isUser ? colors.primary : colors.surfaceVariant,
          borderRadius: BorderRadius.circular(16),
        ),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              message.text,
              style: TextStyle(color: isUser ? Colors.white : colors.onSurfaceVariant),
            ),
            const SizedBox(height: 4),
            Text(
              '${message.timestamp.hour}:${message.timestamp.minute.toString().padLeft(2, '0')}',
              style: TextStyle(
                fontSize: 10,
                color: isUser ? Colors.white70 : colors.onSurfaceVariant.withOpacity(0.7),
              ),
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
