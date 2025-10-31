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
}

