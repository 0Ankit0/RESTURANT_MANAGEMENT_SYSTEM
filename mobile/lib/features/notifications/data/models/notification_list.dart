import 'notification.dart';

class NotificationList {
  final List<AppNotification> items;
  final int total;
  final int unreadCount;

  const NotificationList({
    required this.items,
    required this.total,
    required this.unreadCount,
  });

  factory NotificationList.fromJson(Map<String, dynamic> json) {
    return NotificationList(
      items: (json['items'] as List<dynamic>? ?? [])
          .map((e) => AppNotification.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int? ?? 0,
      unreadCount: json['unread_count'] as int? ?? 0,
    );
  }
}
