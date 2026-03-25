import 'package:mixpanel_flutter/mixpanel_flutter.dart';

import '../analytics_interface.dart';

class MixpanelAnalyticsAdapter implements AnalyticsAdapter {
  MixpanelAnalyticsAdapter._(this._mixpanel);

  final Mixpanel _mixpanel;

  static Future<MixpanelAnalyticsAdapter> init({
    required String token,
    String? serverUrl,
  }) async {
    final mixpanel = await Mixpanel.init(
      token,
      optOutTrackingDefault: false,
      trackAutomaticEvents: false,
    );
    if (serverUrl != null && serverUrl.isNotEmpty) {
      mixpanel.setServerURL(serverUrl);
    }
    return MixpanelAnalyticsAdapter._(mixpanel);
  }

  @override
  Future<void> capture(String event, [Map<String, Object>? properties]) async {
    _mixpanel.track(event, properties: properties);
  }

  @override
  Future<void> identify(String userId, [Map<String, Object>? properties]) async {
    _mixpanel.identify(userId);
    if (properties != null) {
      for (final entry in properties.entries) {
        _mixpanel.getPeople().set(entry.key, entry.value.toString());
      }
    }
  }

  @override
  Future<void> reset() async {
    await _mixpanel.reset();
  }

  @override
  Future<void> screen(String screenName, [Map<String, Object>? properties]) async {
    _mixpanel.track('screen_view', properties: {
      'screen': screenName,
      ...?properties,
    });
  }

  @override
  Future<void> group(
    String groupType,
    String groupKey, [
    Map<String, Object>? properties,
  ]) async {
    _mixpanel.setGroup(groupType, groupKey);
    if (properties != null) {
      for (final entry in properties.entries) {
        _mixpanel.getGroup(groupType, groupKey).set(
              entry.key,
              entry.value.toString(),
            );
      }
    }
  }

  @override
  Future<bool> isFeatureFlagEnabled(
    String flagKey, {
    bool defaultValue = false,
  }) async {
    return defaultValue;
  }

  @override
  Future<Map<String, Object>> getAllFeatureFlags() async {
    return {};
  }

  @override
  Future<void> flush() async {
    await _mixpanel.flush();
  }

  @override
  Future<void> shutdown() async {
    await _mixpanel.flush();
  }
}
