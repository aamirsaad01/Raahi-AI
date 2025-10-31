import 'package:flutter/material.dart';
import '../../routes/app_routes.dart';
import 'models.dart';

class AiChatPage extends StatefulWidget {
  const AiChatPage({super.key});

  @override
  State<AiChatPage> createState() => _AiChatPageState();
}

class _AiChatPageState extends State<AiChatPage> {
  final TextEditingController _messageController = TextEditingController();
  final List<AiChatMessage> _messages = <AiChatMessage>[
    AiChatMessage(
      id: 'welcome',
      isUser: false,
      text: 'Assalam-o-Alaikum! Main aap ka travel companion hoon. Mujhe sawaal pooch sakte hain Urdu, Roman Urdu ya English mein.',
      timestamp: DateTime.now(),
      language: ChatLanguage.romanUrdu,
    ),
  ];

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  void _sendMessage() {
    if (_messageController.text.trim().isEmpty) return;

    setState(() {
      _messages.add(AiChatMessage(
        id: 'user_${DateTime.now().millisecondsSinceEpoch}',
        isUser: true,
        text: _messageController.text.trim(),
        timestamp: DateTime.now(),
      ));

      // Simulate AI response
      Future<void>.delayed(const Duration(milliseconds: 500), () {
        if (!mounted) return;
        setState(() {
          _messages.add(AiChatMessage(
            id: 'ai_${DateTime.now().millisecondsSinceEpoch}',
            isUser: false,
            text: 'Yeh ek sample response hai. Backend integration ke baad real-time answers milenge.',
            timestamp: DateTime.now(),
            language: ChatLanguage.romanUrdu,
          ));
        });
      });
    });

    _messageController.clear();
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
              padding: const EdgeInsets.all(12),
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
                    onPressed: _sendMessage,
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
