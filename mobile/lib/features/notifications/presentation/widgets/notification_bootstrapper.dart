import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/services/push_registration_service.dart';
import '../providers/notification_provider.dart';

class NotificationBootstrapper extends ConsumerStatefulWidget {
  const NotificationBootstrapper({
    required this.child,
    super.key,
  });

  final Widget child;

  @override
  ConsumerState<NotificationBootstrapper> createState() =>
      _NotificationBootstrapperState();
}

class _NotificationBootstrapperState
    extends ConsumerState<NotificationBootstrapper> {
  bool _isSyncing = false;

  Future<void> _syncIfNeeded() async {
    if (_isSyncing) {
      return;
    }

    final authState = ref.read(authNotifierProvider).valueOrNull;
    final prefs = ref.read(notificationPrefsProvider).valueOrNull;
    final pushConfig = ref.read(pushConfigProvider).valueOrNull;
    final devices = ref.read(notificationDevicesProvider).valueOrNull ?? const [];

    if (authState?.isAuthenticated != true ||
        authState?.user == null ||
        prefs?.pushEnabled != true ||
        pushConfig?.provider == null) {
      return;
    }

    _isSyncing = true;
    try {
      final repository = ref.read(notificationRepositoryProvider);
      final service = PushRegistrationService(repository);
      await service.sync(
        config: pushConfig!,
        existingDevices: devices,
        userId: authState!.user!.id.toString(),
      );
      ref.invalidate(notificationDevicesProvider);
    } finally {
      _isSyncing = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final prefs = ref.watch(notificationPrefsProvider);
    final pushConfig = ref.watch(pushConfigProvider);
    ref.watch(notificationDevicesProvider);

    final canAttemptSync = authState.valueOrNull?.isAuthenticated == true &&
        prefs.valueOrNull?.pushEnabled == true &&
        pushConfig.valueOrNull?.provider != null;

    if (canAttemptSync) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          _syncIfNeeded();
        }
      });
    }

    return widget.child;
  }
}
