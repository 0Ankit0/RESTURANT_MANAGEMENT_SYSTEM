import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'analytics_interface.dart';
import 'analytics_service.dart';
import 'adapters/mixpanel_adapter.dart';
import 'adapters/posthog_adapter.dart';

/// Riverpod provider for [AnalyticsService].
///
/// Usage anywhere in the app:
/// ```dart
/// final analytics = ref.read(analyticsServiceProvider);
/// await analytics.capture('my_event');
/// ```
///
/// The provider reads `ANALYTICS_ENABLED` and `ANALYTICS_PROVIDER` from .env.
/// Add new providers to the factory block below — no other files need changing.
final analyticsServiceProvider = Provider<AnalyticsService>((ref) {
  // Return a no-op service if analytics is not yet initialised.
  // The actual service is injected in main() via ProviderContainer overrides.
  return const AnalyticsService(null);
});

/// Call this once in main() before runApp().
///
/// Returns an [AnalyticsService] that should override [analyticsServiceProvider].
///
/// Example:
/// ```dart
/// final analytics = await buildAnalyticsService();
/// runApp(ProviderScope(
///   overrides: [analyticsServiceProvider.overrideWithValue(analytics)],
///   child: App(),
/// ));
/// ```
Future<AnalyticsService> buildAnalyticsService() async {
  final enabled = dotenv.env['ANALYTICS_ENABLED']?.toLowerCase() == 'true';
  if (!enabled) return const AnalyticsService(null);

  final provider = dotenv.env['ANALYTICS_PROVIDER']?.toLowerCase() ?? 'posthog';

  AnalyticsAdapter? adapter;

  // ----------------------------------------------------------------
  // Factory: add new providers here.
  // ----------------------------------------------------------------
  switch (provider) {
    case 'posthog':
      final apiKey = dotenv.env['POSTHOG_API_KEY'];
      final host = dotenv.env['POSTHOG_HOST'] ?? 'https://us.i.posthog.com';
      if (apiKey != null && apiKey.isNotEmpty) {
        adapter = await PostHogAnalyticsAdapter.init(apiKey: apiKey, host: host);
      }
      break;
    case 'mixpanel':
      final token = dotenv.env['MIXPANEL_PROJECT_TOKEN'];
      final host = dotenv.env['MIXPANEL_API_HOST'];
      if (token != null && token.isNotEmpty) {
        adapter = await MixpanelAnalyticsAdapter.init(token: token, serverUrl: host);
      }
      break;
    default:
      break;
  }

  return AnalyticsService(adapter);
}
