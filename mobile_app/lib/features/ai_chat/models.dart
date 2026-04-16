enum ChatLanguage { urdu, romanUrdu, english }

class AiChatMessage {
  final String id;
  final bool isUser;
  final String text;
  final DateTime timestamp;
  final ChatLanguage? language;

  const AiChatMessage({
    required this.id,
    required this.isUser,
    required this.text,
    required this.timestamp,
    this.language,
  });
}

class ChatConversation {
  final String id;
  final String title;
  final DateTime lastMessageTime;
  final int messageCount;

  const ChatConversation({
    required this.id,
    required this.title,
    required this.lastMessageTime,
    required this.messageCount,
  });

  factory ChatConversation.fromJson(Map<String, dynamic> json) {
    final id = (json['session_id'] ?? json['id'] ?? '').toString();
    final title = (json['title'] as String?)?.trim();
    final tsRaw = (json['last_message_at'] ?? json['updated_at'] ?? '').toString();
    DateTime parsed;
    try {
      parsed = DateTime.parse(tsRaw);
    } catch (_) {
      parsed = DateTime.now();
    }
    return ChatConversation(
      id: id,
      title: (title == null || title.isEmpty) ? 'New chat' : title,
      lastMessageTime: parsed,
      messageCount: (json['message_count'] as num?)?.toInt() ?? 0,
    );
  }
}

