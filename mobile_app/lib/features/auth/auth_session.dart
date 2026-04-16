import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'models.dart';

class AuthSession {
  static const String _keyUserJson = 'auth_user_json';

  static Future<void> save(AuthUser user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyUserJson, jsonEncode(user.toJson()));
  }

  static Future<AuthUser?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_keyUserJson);
    if (raw == null || raw.isEmpty) return null;
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      return AuthUser.fromJson(map);
    } catch (_) {
      return null;
    }
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyUserJson);
  }
}

