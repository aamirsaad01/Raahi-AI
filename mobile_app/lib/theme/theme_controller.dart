import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Global app-wide theme controller.
///
/// Persists the user's selected [ThemeMode] in `SharedPreferences` so the
/// app remembers it across launches.  A single instance is exposed via
/// [themeController] and consumed by `MaterialApp` through an
/// [AnimatedBuilder] in `main.dart`.
class ThemeController extends ChangeNotifier {
  ThemeController._();

  static final ThemeController instance = ThemeController._();

  static const String _prefsKey = 'app_theme_mode';

  ThemeMode _mode = ThemeMode.light;
  bool _loaded = false;

  ThemeMode get mode => _mode;
  bool get isDark => _mode == ThemeMode.dark;
  bool get isLoaded => _loaded;

  Future<void> load() async {
    if (_loaded) return;
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      final String? raw = prefs.getString(_prefsKey);
      switch (raw) {
        case 'dark':
          _mode = ThemeMode.dark;
          break;
        case 'system':
          _mode = ThemeMode.system;
          break;
        case 'light':
        default:
          _mode = ThemeMode.light;
      }
    } catch (_) {
      _mode = ThemeMode.light;
    }
    _loaded = true;
    notifyListeners();
  }

  Future<void> setMode(ThemeMode mode) async {
    if (_mode == mode) return;
    _mode = mode;
    notifyListeners();
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefsKey, _serialize(mode));
    } catch (_) {
      // Persistence is best-effort; ignore I/O errors so the toggle still
      // works for the current session.
    }
  }

  Future<void> toggleDark(bool useDark) {
    return setMode(useDark ? ThemeMode.dark : ThemeMode.light);
  }

  static String _serialize(ThemeMode mode) {
    switch (mode) {
      case ThemeMode.dark:
        return 'dark';
      case ThemeMode.system:
        return 'system';
      case ThemeMode.light:
        return 'light';
    }
  }
}

/// Convenience accessor.
ThemeController get themeController => ThemeController.instance;
