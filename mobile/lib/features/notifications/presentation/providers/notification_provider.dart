import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/models/notification_list.dart';
import '../../data/models/notification_device.dart';
import '../../data/models/notification_preference.dart';
import '../../data/models/push_config.dart';
import '../../data/repositories/notification_repository.dart';

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  return NotificationRepository(ref.watch(dioClientProvider));
});

final unreadCountProvider = FutureProvider<int>((ref) async {
  final repo = ref.watch(notificationRepositoryProvider);
  final result = await repo.getNotifications(unreadOnly: true, limit: 1);
  return result.unreadCount;
});

final notificationsProvider =
    FutureProvider.family<NotificationList, ({bool unreadOnly})>(
  (ref, params) => ref
      .watch(notificationRepositoryProvider)
      .getNotifications(unreadOnly: params.unreadOnly),
);

final notificationPrefsProvider = FutureProvider<NotificationPreference>((ref) {
  final authState = ref.watch(authNotifierProvider).valueOrNull;
  if (authState?.isAuthenticated != true) {
    return const NotificationPreference(
      emailEnabled: false,
      pushEnabled: false,
      smsEnabled: false,
      websocketEnabled: true,
    );
  }
  return ref.watch(notificationRepositoryProvider).getPreferences();
});

final notificationDevicesProvider = FutureProvider<List<NotificationDevice>>((ref) {
  final authState = ref.watch(authNotifierProvider).valueOrNull;
  if (authState?.isAuthenticated != true) {
    return const <NotificationDevice>[];
  }
  return ref.watch(notificationRepositoryProvider).getDevices();
});

final pushConfigProvider = FutureProvider<PushConfig>((ref) {
  return ref.watch(notificationRepositoryProvider).getPushConfig().catchError((_) {
    return const PushConfig(
      provider: null,
      webpush: PushProviderConfig(enabled: false),
      fcm: PushProviderConfig(enabled: false),
      onesignal: PushProviderConfig(enabled: false),
    );
  });
});
