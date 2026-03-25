/// Analytics Strategy interface for Flutter.
///
/// Every analytics provider (PostHog, Mixpanel, Amplitude, custom…) must
/// extend [AnalyticsAdapter].  [AnalyticsService] depends only on this
/// contract — swapping providers requires only a new adapter class.
///
/// Pattern notes:
/// - **Strategy** : [AnalyticsAdapter] defines the operation family.
///   [AnalyticsService] holds an adapter and delegates to it.
/// - **Adapter**  : Concrete classes (e.g. [PostHogAnalyticsAdapter]) wrap
///   third-party SDKs, adapting their API to this interface.
abstract class AnalyticsAdapter {
  // ------------------------------------------------------------------
  // Sending (write) operations
  // ------------------------------------------------------------------

  /// Record a named event with optional properties.
  Future<void> capture(String event, [Map<String, Object>? properties]);

  /// Attach persistent traits to a person.
  Future<void> identify(String userId, [Map<String, Object>? properties]);

  /// Disassociate the current user (e.g. on logout).
  Future<void> reset();

  /// Record a screen / page view.
  Future<void> screen(String screenName, [Map<String, Object>? properties]);

  /// Associate the user with a group (e.g. organisation / tenant).
  Future<void> group(
    String groupType,
    String groupKey, [
    Map<String, Object>? properties,
  ]);

  // ------------------------------------------------------------------
  // Retrieving (read) operations
  // ------------------------------------------------------------------

  /// Return the value of a feature flag, or [defaultValue] on failure.
  Future<bool> isFeatureFlagEnabled(String flagKey, {bool defaultValue = false});

  /// Return all feature flags for the current user.
  Future<Map<String, Object>> getAllFeatureFlags();

  // ------------------------------------------------------------------
  // Lifecycle
  // ------------------------------------------------------------------

  /// Flush any buffered events immediately.
  Future<void> flush();

  /// Clean shutdown — flush and close resources.
  Future<void> shutdown();
}
