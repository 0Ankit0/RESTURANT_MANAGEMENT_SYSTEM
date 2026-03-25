class NotificationDevice {
  const NotificationDevice({
    required this.id,
    required this.provider,
    required this.platform,
    required this.isActive,
    required this.lastSeenAt,
    required this.createdAt,
    this.token,
    this.endpoint,
    this.subscriptionId,
  });

  final int id;
  final String provider;
  final String platform;
  final bool isActive;
  final DateTime lastSeenAt;
  final DateTime createdAt;
  final String? token;
  final String? endpoint;
  final String? subscriptionId;

  factory NotificationDevice.fromJson(Map<String, dynamic> json) {
    return NotificationDevice(
      id: json['id'] as int,
      provider: json['provider'] as String,
      platform: json['platform'] as String,
      isActive: json['is_active'] as bool? ?? true,
      lastSeenAt: DateTime.parse(json['last_seen_at'] as String),
      createdAt: DateTime.parse(json['created_at'] as String),
      token: json['token'] as String?,
      endpoint: json['endpoint'] as String?,
      subscriptionId: json['subscription_id'] as String?,
    );
  }
}
