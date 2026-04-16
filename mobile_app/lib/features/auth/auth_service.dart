import 'dart:convert';
import 'package:http/http.dart' as http;

import 'models.dart';

class AuthService {
  static const String baseUrl = 'https://coronary-haste-zombie.ngrok-free.dev';

  Future<AuthUser> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(<String, dynamic>{
        'email': email.trim(),
        'password': password,
      }),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      return AuthUser.fromJson(body['user'] as Map<String, dynamic>);
    }
    throw Exception(body['error'] ?? 'Login failed');
  }

  Future<void> register({
    required String name,
    required String email,
    required String contactNumber,
    required String dob,
    required String cnic,
    required String password,
    String medicalConditions = '',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/register'),
      headers: <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(<String, dynamic>{
        'name': name.trim(),
        'email': email.trim(),
        'contact_number': contactNumber.trim(),
        'dob': dob.trim(),
        'cnic': cnic.trim(),
        'medical_conditions': medicalConditions.trim(),
        'password': password,
      }),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 201 && body['success'] == true) return;
    throw Exception(body['error'] ?? 'Signup failed');
  }

  Future<List<AuthUser>> getAllUsers({required String adminEmail}) async {
    final uri = Uri.parse('$baseUrl/api/auth/users').replace(
      queryParameters: <String, String>{'admin_email': adminEmail},
    );
    final response = await http.get(uri);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) {
      final items = body['users'] as List<dynamic>? ?? <dynamic>[];
      return items
          .map((dynamic e) => AuthUser.fromJson(e as Map<String, dynamic>))
          .toList();
    }
    throw Exception(body['error'] ?? 'Failed to fetch users');
  }

  Future<void> updateUser({
    required int userId,
    required String adminEmail,
    required Map<String, dynamic> updates,
  }) async {
    final payload = <String, dynamic>{...updates, 'admin_email': adminEmail};
    final response = await http.put(
      Uri.parse('$baseUrl/api/auth/users/$userId'),
      headers: <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) return;
    throw Exception(body['error'] ?? 'Failed to update user');
  }

  Future<void> deleteUser({
    required int userId,
    required String adminEmail,
  }) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/api/auth/users/$userId'),
      headers: <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(<String, dynamic>{'admin_email': adminEmail}),
    );
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode == 200 && body['success'] == true) return;
    throw Exception(body['error'] ?? 'Failed to delete user');
  }
}

