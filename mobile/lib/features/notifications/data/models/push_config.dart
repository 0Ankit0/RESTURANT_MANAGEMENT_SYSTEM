class PushProviderConfig {
  const PushProviderConfig({
    required this.enabled,
    this.vapidPublicKey,
    this.projectId,
    this.webVapidKey,
    this.apiKey,
    this.appId,
    this.messagingSenderId,
    this.authDomain,
    this.storageBucket,
    this.measurementId,
    this.webAppId,
  });

  final bool enabled;
  final String? vapidPublicKey;
  final String? projectId;
  final String? webVapidKey;
  final String? apiKey;
  final String? appId;
  final String? messagingSenderId;
  final String? authDomain;
  final String? storageBucket;
  final String? measurementId;
  final String? webAppId;

  factory PushProviderConfig.fromJson(Map<String, dynamic> json) {
    return PushProviderConfig(
      enabled: json['enabled'] as bool? ?? false,
      vapidPublicKey: json['vapid_public_key'] as String?,
      projectId: json['project_id'] as String?,
      webVapidKey: json['web_vapid_key'] as String?,
      apiKey: json['api_key'] as String?,
      appId: json['app_id'] as String?,
      messagingSenderId: json['messaging_sender_id'] as String?,
      authDomain: json['auth_domain'] as String?,
      storageBucket: json['storage_bucket'] as String?,
      measurementId: json['measurement_id'] as String?,
      webAppId: json['web_app_id'] as String?,
    );
  }
}

class PushConfig {
  const PushConfig({
    required this.provider,
    required this.webpush,
    required this.fcm,
    required this.onesignal,
  });

  final String? provider;
  final PushProviderConfig webpush;
  final PushProviderConfig fcm;
  final PushProviderConfig onesignal;

  factory PushConfig.fromJson(Map<String, dynamic> json) {
    final providers = json['providers'] as Map<String, dynamic>? ?? {};
    return PushConfig(
      provider: json['provider'] as String?,
      webpush: PushProviderConfig.fromJson(
        (providers['webpush'] as Map<String, dynamic>?) ?? {},
      ),
      fcm: PushProviderConfig.fromJson(
        (providers['fcm'] as Map<String, dynamic>?) ?? {},
      ),
      onesignal: PushProviderConfig.fromJson(
        (providers['onesignal'] as Map<String, dynamic>?) ?? {},
      ),
    );
  }
}
