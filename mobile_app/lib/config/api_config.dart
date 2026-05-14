/// Single source of truth for the Raahi backend base URL.
///
/// Default: production Render deployment. Override for local/ngrok builds:
///
/// ```bash
/// flutter run --dart-define=API_BASE_URL=https://your-host.example.com
/// ```
///
/// Trailing slashes are stripped so callers can safely use `'${ApiConfig.baseUrl}/api/...'`.
class ApiConfig {
  ApiConfig._();

  static const String _defaultBaseUrl = 'https://raahi-ai-b3p8.onrender.com';

  static String get baseUrl {
    const String fromEnv = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: '',
    );
    final String raw = fromEnv.trim().isEmpty ? _defaultBaseUrl : fromEnv.trim();
    if (raw.endsWith('/')) {
      return raw.substring(0, raw.length - 1);
    }
    return raw;
  }
}
