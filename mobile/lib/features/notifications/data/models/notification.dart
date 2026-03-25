enum NotificationType {
  info,
  success,
  warning,
  error,
  payment,
  auth,
  system;

  static NotificationType fromString(String v) {
    return NotificationType.values.firstWhere(
      (e) => e.name == v,
      orElse: () => NotificationType.info,
    );
  }
}

class AppNotification {
  final String id;
  final String userId;
  final String title;
  final String body;
  final NotificationType type;
  final bool isRead;
  final dynamic extraData;
  final String createdAt;

  const AppNotification({
    required this.id,
    required this.userId,
    required this.title,
    required this.body,
    required this.type,
    required this.isRead,
    this.extraData,
    required this.createdAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'].toString(),
      userId: json['user_id']?.toString() ?? '',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      type: NotificationType.fromString(json['type'] as String? ?? 'info'),
      isRead: json['is_read'] as bool? ?? false,
      extraData: json['extra_data'],
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}
