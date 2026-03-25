import 'dart:developer' as developer;
import 'analytics_interface.dart';

/// AnalyticsService — the public API consumed by the rest of the Flutter app.
///
/// This is the *Context* in the Strategy pattern.  It holds a reference to
/// an [AnalyticsAdapter] and delegates every operation to it.  When analytics
/// are disabled (adapter is null) all methods silently no-op.
class AnalyticsService {
  final AnalyticsAdapter? _adapter;

  const AnalyticsService(this._adapter);

  bool get enabled => _adapter != null;

  // ------------------------------------------------------------------
  // Sending operations
  // ------------------------------------------------------------------

  Future<void> capture(String event, [Map<String, Object>? properties]) async {
    try {
      await _adapter?.capture(event, properties);
    } catch (e) {
      developer.log('Analytics capture error: $e', name: 'Analytics');
    }
  }

  Future<void> identify(String userId, [Map<String, Object>? properties]) async {
    try {
      await _adapter?.identify(userId, properties);
    } catch (e) {
      developer.log('Analytics identify error: $e', name: 'Analytics');
    }
  }

  Future<void> reset() async {
    try {
      await _adapter?.reset();
    } catch (e) {
      developer.log('Analytics reset error: $e', name: 'Analytics');
    }
  }

  Future<void> screen(String screenName, [Map<String, Object>? properties]) async {
    try {
      await _adapter?.screen(screenName, properties);
    } catch (e) {
      developer.log('Analytics screen error: $e', name: 'Analytics');
    }
  }

  Future<void> group(
    String groupType,
    String groupKey, [
    Map<String, Object>? properties,
  ]) async {
    try {
      await _adapter?.group(groupType, groupKey, properties);
    } catch (e) {
      developer.log('Analytics group error: $e', name: 'Analytics');
    }
  }

  // ------------------------------------------------------------------
  // Retrieving operations
  // ------------------------------------------------------------------

  Future<bool> isFeatureFlagEnabled(
    String flagKey, {
    bool defaultValue = false,
  }) async {
    try {
      return await _adapter?.isFeatureFlagEnabled(flagKey, defaultValue: defaultValue) ??
          defaultValue;
    } catch (e) {
      developer.log('Analytics isFeatureFlagEnabled error: $e', name: 'Analytics');
      return defaultValue;
    }
  }

  Future<Map<String, Object>> getAllFeatureFlags() async {
    try {
      return await _adapter?.getAllFeatureFlags() ?? {};
    } catch (e) {
      developer.log('Analytics getAllFeatureFlags error: $e', name: 'Analytics');
      return {};
    }
  }

  // ------------------------------------------------------------------
  // Lifecycle
  // ------------------------------------------------------------------

  Future<void> flush() async {
    try {
      await _adapter?.flush();
    } catch (e) {
      developer.log('Analytics flush error: $e', name: 'Analytics');
    }
  }

  Future<void> shutdown() async {
    try {
      await _adapter?.shutdown();
    } catch (e) {
      developer.log('Analytics shutdown error: $e', name: 'Analytics');
    }
  }
}
