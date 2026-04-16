/// Geoapify API key for map tiles and routing on the itinerary map.
///
/// **Do not commit real keys.** Pass at build time:
/// `flutter run --dart-define=GEOAPIFY_API_KEY=your_key`
///
/// Use the same Geoapify project as the backend (`GEOAPIFY_API_KEY` in `.env`).
/// Restrict the key by app bundle ID / signing cert in Geoapify MyProjects
/// when possible.
const String kGeoapifyApiKey =
    String.fromEnvironment('GEOAPIFY_API_KEY', defaultValue: '');

bool get kHasGeoapifyKey => kGeoapifyApiKey.isNotEmpty;
