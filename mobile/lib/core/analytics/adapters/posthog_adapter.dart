import 'package:posthog_flutter/posthog_flutter.dart';
import '../analytics_interface.dart';

/// PostHog analytics adapter.
///
/// Adapts the posthog_flutter SDK to the [AnalyticsAdapter] interface.
///
/// To add a new provider (e.g. Mixpanel):
///   1. Create adapters/mixpanel_adapter.dart implementing AnalyticsAdapter.
///   2. Register it in analytics_provider.dart factory logic.
class PostHogAnalyticsAdapter implements AnalyticsAdapter {
  PostHogAnalyticsAdapter._();

  static Future<PostHogAnalyticsAdapter> init({
    required String apiKey,
    required String host,
  }) async {
    final config = PostHogConfig(apiKey)
      ..host = host
      // Disable automatic lifecycle events — we capture events explicitly
      ..captureApplicationLifecycleEvents = false;

    await Posthog().setup(config);
    return PostHogAnalyticsAdapter._();
  }

  @override
  Future<void> capture(String event, [Map<String, Object>? properties]) async {
    await Posthog().capture(
      eventName: event,
      properties: properties,
    );
  }

  @override
  Future<void> identify(String userId, [Map<String, Object>? properties]) async {
    await Posthog().identify(
      userId: userId,
      userProperties: properties,
    );
  }

  @override
  Future<void> reset() async {
    await Posthog().reset();
  }

  @override
  Future<void> screen(String screenName, [Map<String, Object>? properties]) async {
    await Posthog().screen(
      screenName: screenName,
      properties: properties,
    );
  }

  @override
  Future<void> group(
    String groupType,
    String groupKey, [
    Map<String, Object>? properties,
  ]) async {
    await Posthog().group(
      groupType: groupType,
      groupKey: groupKey,
      groupProperties: properties,
    );
  }

  @override
  Future<bool> isFeatureFlagEnabled(
    String flagKey, {
    bool defaultValue = false,
  }) async {
    try {
      final result = await Posthog().isFeatureEnabled(flagKey);
      return result;
    } catch (_) {
      return defaultValue;
    }
  }

  @override
  Future<Map<String, Object>> getAllFeatureFlags() async {
    // posthog_flutter v4 does not expose a bulk getAllFlags method.
    // Return an empty map; override this in a custom adapter if needed.
    return {};
  }

  @override
  Future<void> flush() async {
    await Posthog().flush();
  }

  @override
  Future<void> shutdown() async {
    // posthog_flutter does not expose an explicit shutdown; flush is sufficient
    await Posthog().flush();
  }
}
