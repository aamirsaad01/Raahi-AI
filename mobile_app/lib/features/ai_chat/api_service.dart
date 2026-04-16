import 'dart:convert';
import 'package:http/http.dart' as http;

import 'models.dart';

class AiChatApiService {
  static const String baseUrl = 'https://coronary-haste-zombie.ngrok-free.dev';

  Future<Map<String, dynamic>> sendMessage({
    required int userId,
    required String message,
    int? sessionId,
    int? itineraryId,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/chat/send'),
      headers: <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(<String, dynamic>{
        'user_id': userId,
        'message': message,
        if (sessionId != null) 'session_id': sessionId,
        if (itineraryId != null) 'itinerary_id': itineraryId,
      }),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) return body;
    throw Exception(body['error'] ?? 'Failed to send message');
  }

  Future<List<ChatConversation>> getSessions(int userId) async {
    final uri = Uri.parse('$baseUrl/api/chat/sessions')
        .replace(queryParameters: <String, String>{'user_id': '$userId'});
    final response = await http.get(uri);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final rows = body['sessions'] as List<dynamic>? ?? <dynamic>[];
      return rows
          .map((dynamic e) => ChatConversation.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    throw Exception(body['error'] ?? 'Failed to fetch sessions');
  }

  Future<List<AiChatMessage>> getMessages({
    required int userId,
    required int sessionId,
  }) async {
    final uri = Uri.parse('$baseUrl/api/chat/sessions/$sessionId/messages')
        .replace(queryParameters: <String, String>{'user_id': '$userId'});
    final response = await http.get(uri);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final rows = body['messages'] as List<dynamic>? ?? <dynamic>[];
      return rows.map((dynamic e) {
        final m = e as Map<String, dynamic>;
        final isUser = (m['role'] ?? 'user').toString().toLowerCase() == 'user';
        DateTime ts;
        try {
          ts = DateTime.parse((m['created_at'] ?? '').toString());
        } catch (_) {
          ts = DateTime.now();
        }
        return AiChatMessage(
          id: (m['message_id'] ?? '').toString(),
          isUser: isUser,
          text: (m['content'] ?? '').toString(),
          timestamp: ts,
          language: isUser ? null : ChatLanguage.romanUrdu,
        );
      }).toList();
    }
    throw Exception(body['error'] ?? 'Failed to fetch messages');
  }
}

