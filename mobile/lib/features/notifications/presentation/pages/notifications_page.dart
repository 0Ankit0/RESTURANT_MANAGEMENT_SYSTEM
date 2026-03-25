import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/error/error_handler.dart';
import '../../data/models/notification.dart';
import '../../data/models/notification_list.dart';
import '../providers/notification_provider.dart';

class _NotificationFilter {
  static const String all = 'all';
  static const String unread = 'unread';
}

final _filterProvider = StateProvider<String>((ref) => _NotificationFilter.all);

final _notificationsPageProvider =
    FutureProvider.autoDispose<NotificationList>((ref) async {
  final unreadOnly =
      ref.watch(_filterProvider) == _NotificationFilter.unread;
  return ref
      .watch(notificationRepositoryProvider)
      .getNotifications(unreadOnly: unreadOnly);
});

class NotificationsPage extends ConsumerWidget {
  const NotificationsPage({super.key});

  String _timeAgo(String dateStr) {
    try {
      final dt = DateTime.parse(dateStr).toLocal();
      final diff = DateTime.now().difference(dt);
      if (diff.inDays > 0) return '${diff.inDays}d ago';
      if (diff.inHours > 0) return '${diff.inHours}h ago';
      if (diff.inMinutes > 0) return '${diff.inMinutes}m ago';
      return 'Just now';
    } catch (_) {
      return '';
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notificationsAsync = ref.watch(_notificationsPageProvider);
    final filter = ref.watch(_filterProvider);
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          IconButton(
            icon: const Icon(Icons.done_all_outlined),
            tooltip: 'Mark all read',
            onPressed: () async {
              try {
                await ref
                    .read(notificationRepositoryProvider)
                    .markAllRead();
                ref.invalidate(_notificationsPageProvider);
                ref.invalidate(unreadCountProvider);
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(ErrorHandler.handle(e).message),
                      backgroundColor: Colors.red,
                    ),
                  );
                }
              }
            },
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Row(
              children: [
                _FilterChip(
                  label: 'All',
                  selected: filter == _NotificationFilter.all,
                  onSelected: () => ref
                      .read(_filterProvider.notifier)
                      .state = _NotificationFilter.all,
                ),
                const SizedBox(width: 8),
                _FilterChip(
                  label: 'Unread',
                  selected: filter == _NotificationFilter.unread,
                  onSelected: () => ref
                      .read(_filterProvider.notifier)
                      .state = _NotificationFilter.unread,
                ),
              ],
            ),
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(_notificationsPageProvider);
          ref.invalidate(unreadCountProvider);
        },
        child: notificationsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: Colors.red),
                const SizedBox(height: 12),
                Text(ErrorHandler.handle(err).message,
                    textAlign: TextAlign.center),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: () => ref.invalidate(_notificationsPageProvider),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
          data: (data) {
            final items = data.items;

            if (items.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.notifications_none_outlined,
                        size: 64,
                        color: colorScheme.onSurface.withValues(alpha: 0.3)),
                    const SizedBox(height: 16),
                    Text(
                      filter == _NotificationFilter.unread
                          ? 'No unread notifications'
                          : 'No notifications yet',
                      style: TextStyle(
                          color:
                              colorScheme.onSurface.withValues(alpha: 0.5)),
                    ),
                  ],
                ),
              );
            }

            return ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final notification = items[index];
                return _NotificationTile(
                  notification: notification,
                  timeAgo: _timeAgo(notification.createdAt),
                  onMarkRead: () async {
                    try {
                      await ref
                          .read(notificationRepositoryProvider)
                          .markRead(notification.id);
                      ref.invalidate(_notificationsPageProvider);
                      ref.invalidate(unreadCountProvider);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(ErrorHandler.handle(e).message),
                            backgroundColor: Colors.red,
                          ),
                        );
                      }
                    }
                  },
                  onDelete: () async {
                    try {
                      await ref
                          .read(notificationRepositoryProvider)
                          .deleteNotification(notification.id);
                      ref.invalidate(_notificationsPageProvider);
                      ref.invalidate(unreadCountProvider);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(ErrorHandler.handle(e).message),
                            backgroundColor: Colors.red,
                          ),
                        );
                      }
                    }
                  },
                )
                    .animate()
                    .fadeIn(
                        delay: Duration(milliseconds: index * 40))
                    .slideY(begin: 0.05);
              },
            );
          },
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onSelected;

  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onSelected(),
      visualDensity: VisualDensity.compact,
    );
  }
}

class _NotificationTile extends StatelessWidget {
  final AppNotification notification;
  final String timeAgo;
  final VoidCallback onMarkRead;
  final VoidCallback onDelete;

  const _NotificationTile({
    required this.notification,
    required this.timeAgo,
    required this.onMarkRead,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isUnread = !notification.isRead;

    return Dismissible(
      key: Key(notification.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 16),
        decoration: BoxDecoration(
          color: Colors.red,
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(Icons.delete_outline, color: Colors.white),
      ),
      onDismissed: (_) => onDelete(),
      child: Container(
        decoration: BoxDecoration(
          color: isUnread
              ? colorScheme.primary.withValues(alpha: 0.08)
              : colorScheme.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isUnread
                ? colorScheme.primary.withValues(alpha: 0.3)
                : colorScheme.outline.withValues(alpha: 0.2),
          ),
        ),
        child: ListTile(
          leading: CircleAvatar(
            backgroundColor: isUnread
                ? colorScheme.primary.withValues(alpha: 0.15)
                : colorScheme.onSurface.withValues(alpha: 0.08),
            child: Icon(
              isUnread
                  ? Icons.notifications_active_outlined
                  : Icons.notifications_none_outlined,
              color: isUnread ? colorScheme.primary : Colors.grey,
              size: 20,
            ),
          ),
          title: Text(
            notification.title,
            style: TextStyle(
              fontWeight: isUnread ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (notification.body.isNotEmpty) ...[
                const SizedBox(height: 2),
                Text(
                  notification.body,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13),
                ),
              ],
              const SizedBox(height: 4),
              Text(
                timeAgo,
                style: TextStyle(
                    fontSize: 11,
                    color: colorScheme.onSurface.withValues(alpha: 0.5)),
              ),
            ],
          ),
          trailing: isUnread
              ? IconButton(
                  icon: const Icon(Icons.check_circle_outline,
                      color: Colors.green, size: 20),
                  tooltip: 'Mark as read',
                  onPressed: onMarkRead,
                )
              : IconButton(
                  icon: Icon(Icons.delete_outline,
                      color: Colors.red.withValues(alpha: 0.7), size: 20),
                  tooltip: 'Delete',
                  onPressed: onDelete,
                ),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        ),
      ),
    );
  }
}
