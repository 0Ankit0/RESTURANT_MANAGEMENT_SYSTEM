class NotificationPreference {
  final int? id;
  final int? userId;
  final bool emailEnabled;
  final bool pushEnabled;
  final bool smsEnabled;
  final bool websocketEnabled;
  final String? pushEndpoint;
  final String? pushProvider;

  const NotificationPreference({
    this.id,
    this.userId,
    required this.emailEnabled,
    required this.pushEnabled,
    required this.smsEnabled,
    required this.websocketEnabled,
    this.pushEndpoint,
    this.pushProvider,
  });

  factory NotificationPreference.fromJson(Map<String, dynamic> json) {
    return NotificationPreference(
      id: json['id'] as int?,
      userId: json['user_id'] as int?,
      emailEnabled: json['email_enabled'] as bool? ?? true,
      pushEnabled: json['push_enabled'] as bool? ?? true,
      smsEnabled: json['sms_enabled'] as bool? ?? false,
      websocketEnabled: json['websocket_enabled'] as bool? ?? true,
      pushEndpoint: json['push_endpoint'] as String?,
      pushProvider: json['push_provider'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'email_enabled': emailEnabled,
        'push_enabled': pushEnabled,
        'sms_enabled': smsEnabled,
        'websocket_enabled': websocketEnabled,
      };

  NotificationPreference copyWith({
    bool? emailEnabled,
    bool? pushEnabled,
    bool? smsEnabled,
    bool? websocketEnabled,
    String? pushEndpoint,
    String? pushProvider,
  }) {
    return NotificationPreference(
      id: id,
      userId: userId,
      emailEnabled: emailEnabled ?? this.emailEnabled,
      pushEnabled: pushEnabled ?? this.pushEnabled,
      smsEnabled: smsEnabled ?? this.smsEnabled,
      websocketEnabled: websocketEnabled ?? this.websocketEnabled,
      pushEndpoint: pushEndpoint ?? this.pushEndpoint,
      pushProvider: pushProvider ?? this.pushProvider,
    );
  }
}
