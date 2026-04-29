import 'dart:convert';
import 'package:http/http.dart' as http;

class EmergencyContactRecord {
  final int contactId;
  final int itineraryId;
  final String contactName;
  final String relationship;
  final String phoneNumber;

  const EmergencyContactRecord({
    required this.contactId,
    required this.itineraryId,
    required this.contactName,
    required this.relationship,
    required this.phoneNumber,
  });

  factory EmergencyContactRecord.fromJson(Map<String, dynamic> json) {
    return EmergencyContactRecord(
      contactId: (json['contact_id'] as num?)?.toInt() ?? 0,
      itineraryId: (json['itinerary_id'] as num?)?.toInt() ?? 0,
      contactName: (json['contact_name'] ?? '').toString(),
      relationship: (json['relationship'] ?? '').toString(),
      phoneNumber: (json['phone_number'] ?? '').toString(),
    );
  }
}

class EmergencyContactService {
  static const String baseUrl = 'https://coronary-haste-zombie.ngrok-free.dev';

  Future<void> saveForItinerary({
    required int itineraryId,
    required String contactName,
    required String relationship,
    required String phoneNumber,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/emergency/contacts'),
      headers: <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(<String, dynamic>{
        'itinerary_id': itineraryId,
        'contact_name': contactName.trim(),
        'relationship': relationship.trim(),
        'phone_number': phoneNumber.trim(),
      }),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 201 && body['success'] == true) return;
    throw Exception(body['error'] ?? 'Failed to save emergency contact');
  }

  Future<EmergencyContactRecord?> getLatestLinkedForUser(int userId) async {
    final uri = Uri.parse('$baseUrl/api/emergency/linked-contact')
        .replace(queryParameters: <String, String>{'user_id': '$userId'});
    final response = await http.get(uri);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final contact = body['contact'];
      if (contact is Map<String, dynamic>) {
        return EmergencyContactRecord.fromJson(contact);
      }
      return null;
    }
    throw Exception(body['error'] ?? 'Failed to fetch emergency contact');
  }

  Future<List<EmergencyContactRecord>> getContactsForLatestItineraryForUser(
    int userId,
  ) async {
    final uri = Uri.parse('$baseUrl/api/emergency/contacts')
        .replace(queryParameters: <String, String>{'user_id': '$userId'});
    final response = await http.get(uri);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final List<dynamic> rows = body['contacts'] as List<dynamic>? ?? <dynamic>[];
      return rows
          .whereType<Map<String, dynamic>>()
          .map(EmergencyContactRecord.fromJson)
          .toList();
    }
    throw Exception(body['error'] ?? 'Failed to fetch emergency contacts');
  }
}

