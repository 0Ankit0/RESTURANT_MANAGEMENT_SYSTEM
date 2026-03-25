import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/models/general_setting.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../../core/providers/system_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../notifications/data/services/push_registration_service.dart';
import '../../../notifications/presentation/providers/notification_provider.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.person_outline), text: 'Account'),
            Tab(
                icon: Icon(Icons.notifications_outlined),
                text: 'Notifications'),
            Tab(icon: Icon(Icons.security_outlined), text: 'Privacy'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          _AccountTab(),
          _NotificationsTab(),
          _PrivacyTab(),
        ],
      ),
    );
  }
}

// ─── Account Tab ───────────────────────────────────────────────────────────────

class _AccountTab extends ConsumerStatefulWidget {
  const _AccountTab();

  @override
  ConsumerState<_AccountTab> createState() => _AccountTabState();
}

class _AccountTabState extends ConsumerState<_AccountTab> {
  bool _sendingVerification = false;

  Future<void> _resendVerification() async {
    setState(() => _sendingVerification = true);
    try {
      final dio = ref.read(dioClientProvider).dio;
      await dio.post(ApiEndpoints.resendVerification);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Verification email sent!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(ErrorHandler.handle(e).message),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _sendingVerification = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final generalSettingsAsync = ref.watch(systemGeneralSettingsProvider);
    final user = authState.valueOrNull?.user;

    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }

    String? memberSince;
    if (user.createdAt != null) {
      try {
        final dt = DateTime.parse(user.createdAt!).toLocal();
        memberSince =
            '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
      } catch (_) {
        memberSince = user.createdAt;
      }
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionHeader(label: 'Account Details'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _SettingsRow(
                    icon: Icons.alternate_email,
                    label: 'Username',
                    value: user.username,
                  ),
                  const Divider(height: 16),
                  Row(
                    children: [
                      const Icon(Icons.email_outlined,
                          size: 20, color: Colors.grey),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Email',
                                style: TextStyle(
                                    fontSize: 12, color: Colors.grey)),
                            Text(user.email,
                                style: const TextStyle(
                                    fontWeight: FontWeight.w500)),
                          ],
                        ),
                      ),
                      _StatusBadge(
                        label: user.isConfirmed ? 'Verified' : 'Unverified',
                        color: user.isConfirmed ? Colors.green : Colors.orange,
                      ),
                    ],
                  ),
                  if (!user.isConfirmed) ...[
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed:
                            _sendingVerification ? null : _resendVerification,
                        icon: _sendingVerification
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.send_outlined, size: 16),
                        label: const Text('Resend Verification Email'),
                      ),
                    ),
                  ],
                  const Divider(height: 16),
                  _SettingsRow(
                    icon: Icons.badge_outlined,
                    label: 'Account Type',
                    value: user.isSuperuser ? 'Superuser' : 'Standard',
                    valueColor: user.isSuperuser ? Colors.purple : null,
                  ),
                  if (memberSince != null) ...[
                    const Divider(height: 16),
                    _SettingsRow(
                      icon: Icons.calendar_today_outlined,
                      label: 'Member Since',
                      value: memberSince,
                    ),
                  ],
                ],
              ),
            ),
          ).animate().fadeIn(delay: 100.ms).slideY(begin: 0.05),
          const SizedBox(height: 16),
          const _SectionHeader(label: 'Runtime Configuration'),
          _RuntimeSettingsCard(settingsAsync: generalSettingsAsync)
              .animate()
              .fadeIn(delay: 180.ms)
              .slideY(begin: 0.05),
        ],
      ),
    );
  }
}

// ─── Notifications Tab ─────────────────────────────────────────────────────────

class _NotificationsTab extends ConsumerWidget {
  const _NotificationsTab();

  Future<void> _updatePref(
    WidgetRef ref,
    BuildContext context,
    Map<String, bool> data,
  ) async {
    try {
      await ref.read(notificationRepositoryProvider).updatePreferences(data);
      ref.invalidate(notificationPrefsProvider);
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
  }

  Future<void> _syncCurrentDevice(
    WidgetRef ref,
    BuildContext context,
  ) async {
    try {
      final authState = ref.read(authNotifierProvider).valueOrNull;
      final user = authState?.user;
      if (user == null) {
        throw Exception('Please sign in again to register this device.');
      }
      final repository = ref.read(notificationRepositoryProvider);
      final config = await repository.getPushConfig();
      final devices = await repository.getDevices();
      final service = PushRegistrationService(repository);
      await service.sync(
        config: config,
        existingDevices: devices,
        userId: user.id,
      );
      ref.invalidate(notificationDevicesProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Device registration synced'),
            backgroundColor: Colors.green,
          ),
        );
      }
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
  }

  Future<void> _removeDevice(
    WidgetRef ref,
    BuildContext context,
    int deviceId,
  ) async {
    try {
      await ref.read(notificationRepositoryProvider).deleteDevice(deviceId);
      ref.invalidate(notificationDevicesProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Device removed'),
            backgroundColor: Colors.green,
          ),
        );
      }
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
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final prefsAsync = ref.watch(notificationPrefsProvider);
    final devicesAsync = ref.watch(notificationDevicesProvider);
    final pushConfigAsync = ref.watch(pushConfigProvider);
    final capabilitiesAsync = ref.watch(systemCapabilitiesProvider);

    return prefsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 12),
            Text(ErrorHandler.handle(err).message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () => ref.invalidate(notificationPrefsProvider),
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
      data: (prefs) {
        final devices = devicesAsync.valueOrNull ?? const [];
        final pushProvider = pushConfigAsync.valueOrNull?.provider ??
            prefs.pushProvider ??
            'none';
        final notificationsEnabled =
            capabilitiesAsync.valueOrNull?.modules['notifications'] ?? true;

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _SectionHeader(label: 'Notification Channels'),
              Card(
                child: Column(
                  children: [
                    _ToggleTile(
                      icon: Icons.web_outlined,
                      title: 'In-App',
                      subtitle: 'Receive notifications within the app',
                      value: prefs.websocketEnabled,
                      onChanged: (v) =>
                          _updatePref(ref, context, {'websocket_enabled': v}),
                    ),
                    const Divider(height: 1),
                    _ToggleTile(
                      icon: Icons.email_outlined,
                      title: 'Email',
                      subtitle: 'Receive notifications via email',
                      value: prefs.emailEnabled,
                      onChanged: (v) =>
                          _updatePref(ref, context, {'email_enabled': v}),
                    ),
                    const Divider(height: 1),
                    _ToggleTile(
                      icon: Icons.phone_android_outlined,
                      title: 'Push',
                      subtitle:
                          'Receive push notifications through the active provider',
                      value: prefs.pushEnabled,
                      onChanged: (v) =>
                          _updatePref(ref, context, {'push_enabled': v}),
                    ),
                    const Divider(height: 1),
                    _ToggleTile(
                      icon: Icons.sms_outlined,
                      title: 'SMS',
                      subtitle: 'Receive notifications via SMS',
                      value: prefs.smsEnabled,
                      onChanged: (v) =>
                          _updatePref(ref, context, {'sms_enabled': v}),
                    ),
                  ],
                ),
              ).animate().fadeIn(delay: 100.ms).slideY(begin: 0.05),
              const SizedBox(height: 16),
              const _SectionHeader(label: 'Runtime Status'),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _SettingsRow(
                        icon: Icons.extension_outlined,
                        label: 'Notifications Module',
                        value: notificationsEnabled ? 'Enabled' : 'Disabled',
                      ),
                      const Divider(height: 16),
                      _SettingsRow(
                        icon: Icons.notifications_active_outlined,
                        label: 'Active Push Provider',
                        value: pushProvider.toUpperCase(),
                      ),
                      const Divider(height: 16),
                      _SettingsRow(
                        icon: Icons.devices_outlined,
                        label: 'Registered Devices',
                        value: devices.length.toString(),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: prefs.pushEnabled
                              ? () => _syncCurrentDevice(ref, context)
                              : null,
                          icon: const Icon(Icons.sync),
                          label: const Text('Sync Current Device'),
                        ),
                      ),
                      if (devices.isNotEmpty) ...[
                        const Divider(height: 16),
                        Column(
                          children: devices
                              .map(
                                (device) => Padding(
                                  padding: const EdgeInsets.only(bottom: 8),
                                  child: Container(
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(12),
                                      border: Border.all(
                                          color: Colors.grey.shade200),
                                    ),
                                    padding: const EdgeInsets.all(12),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.smartphone, size: 18),
                                        const SizedBox(width: 10),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                '${device.provider.toUpperCase()} • ${device.platform}',
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.w600,
                                                ),
                                              ),
                                              const SizedBox(height: 2),
                                              Text(
                                                'Last seen ${device.lastSeenAt.toLocal()}',
                                                style: const TextStyle(
                                                  fontSize: 12,
                                                  color: Colors.grey,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                        IconButton(
                                          onPressed: () => _removeDevice(
                                              ref, context, device.id),
                                          icon:
                                              const Icon(Icons.delete_outline),
                                          color: Colors.red,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              )
                              .toList(),
                        ),
                      ] else ...[
                        const Divider(height: 16),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.grey.shade200),
                          ),
                          child: const Text(
                            'No registered push devices yet.',
                            style: TextStyle(fontSize: 13, color: Colors.grey),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ).animate().fadeIn(delay: 180.ms).slideY(begin: 0.05),
            ],
          ),
        );
      },
    );
  }
}

// ─── Privacy Tab ───────────────────────────────────────────────────────────────

class _PrivacyTab extends ConsumerWidget {
  const _PrivacyTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _SectionHeader(label: 'Security'),
          _PrivacyCard(
            icon: Icons.vpn_key_outlined,
            title: 'Active Sessions',
            subtitle: 'View and manage your active login sessions',
            buttonLabel: 'Manage Sessions',
            onTap: () => context.go(AppConstants.tokensRoute),
          ).animate().fadeIn(delay: 100.ms).slideY(begin: 0.05),
          const SizedBox(height: 24),
          const _SectionHeader(label: 'Danger Zone'),
          Card(
            color: Colors.red.withValues(alpha: 0.05),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.red.withValues(alpha: 0.3)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.warning_amber_outlined,
                          color: Colors.red.shade700),
                      const SizedBox(width: 8),
                      Text(
                        'Revoke All Sessions',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.red.shade700,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'This will log you out of all devices and revoke all active sessions.',
                    style: TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        final confirm = await showDialog<bool>(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            title: const Text('Revoke All Sessions'),
                            content: const Text(
                                'This will log you out of all devices. Continue?'),
                            actions: [
                              TextButton(
                                  onPressed: () => Navigator.pop(ctx, false),
                                  child: const Text('Cancel')),
                              TextButton(
                                  onPressed: () => Navigator.pop(ctx, true),
                                  child: const Text('Revoke All',
                                      style: TextStyle(color: Colors.red))),
                            ],
                          ),
                        );
                        if (confirm == true && context.mounted) {
                          try {
                            await ref
                                .read(dioClientProvider)
                                .dio
                                .post(ApiEndpoints.revokeAll);
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('All sessions revoked'),
                                  backgroundColor: Colors.green,
                                ),
                              );
                            }
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
                        }
                      },
                      icon:
                          const Icon(Icons.logout, color: Colors.red, size: 18),
                      label: const Text('Revoke All Sessions',
                          style: TextStyle(color: Colors.red)),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.red),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.05),
        ],
      ),
    );
  }
}

// ─── Shared Widgets ────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String label;

  const _SectionHeader({required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelLarge?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }
}

class _RuntimeSettingsCard extends StatelessWidget {
  const _RuntimeSettingsCard({required this.settingsAsync});

  final AsyncValue<List<GeneralSetting>> settingsAsync;

  static const Map<String, String> _labels = {
    'PROJECT_NAME': 'Project',
    'FEATURE_AUTH': 'Auth',
    'FEATURE_MULTITENANCY': 'Multitenancy',
    'FEATURE_NOTIFICATIONS': 'Notifications',
    'FEATURE_FINANCE': 'Payments',
    'FEATURE_ANALYTICS': 'Analytics',
    'FEATURE_SOCIAL_AUTH': 'Social Login',
    'FEATURE_MAPS': 'Maps',
    'PUSH_PROVIDER': 'Push Provider',
    'MAP_PROVIDER': 'Map Provider',
  };

  String _formatValue(String? value) {
    if (value == null || value.isEmpty) return 'Not set';
    if (value == 'True') return 'Enabled';
    if (value == 'False') return 'Disabled';
    return value;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: settingsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) => Text(
            ErrorHandler.handle(err).message,
            style: const TextStyle(color: Colors.red),
          ),
          data: (settings) {
            final visibleSettings = settings
                .where((item) => _labels.containsKey(item.key))
                .toList();
            final overrideCount =
                settings.where((item) => item.source == 'database').length;

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SettingsRow(
                  icon: Icons.storage_outlined,
                  label: 'Database Overrides',
                  value: overrideCount.toString(),
                ),
                const Divider(height: 16),
                ...visibleSettings.asMap().entries.map((entry) {
                  final item = entry.value;
                  final showDivider = entry.key < visibleSettings.length - 1;

                  return Column(
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: _SettingsRow(
                              icon: item.source == 'database'
                                  ? Icons.dns_outlined
                                  : Icons.settings_ethernet_outlined,
                              label: _labels[item.key] ?? item.key,
                              value: _formatValue(item.effectiveValue),
                            ),
                          ),
                          const SizedBox(width: 8),
                          _StatusBadge(
                            label: item.source == 'database' ? 'DB' : 'ENV',
                            color: item.source == 'database'
                                ? Colors.blue
                                : Colors.grey,
                          ),
                        ],
                      ),
                      if (showDivider) const Divider(height: 16),
                    ],
                  );
                }),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _SettingsRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _SettingsRow({
    required this.icon,
    required this.label,
    required this.value,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: Colors.grey),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: const TextStyle(fontSize: 12, color: Colors.grey)),
              Text(
                value,
                style: TextStyle(
                  fontWeight: FontWeight.w500,
                  color: valueColor,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String label;
  final Color color;

  const _StatusBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style:
            TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }
}

class _ToggleTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _ToggleTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SwitchListTile(
      secondary: Icon(icon, color: Colors.grey),
      title: Text(title),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12)),
      value: value,
      onChanged: onChanged,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
    );
  }
}

class _PrivacyCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String buttonLabel;
  final VoidCallback onTap;

  const _PrivacyCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.buttonLabel,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor:
              Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
          child: Icon(icon,
              color: Theme.of(context).colorScheme.primary, size: 20),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle, style: const TextStyle(fontSize: 12)),
        trailing: TextButton(onPressed: onTap, child: Text(buttonLabel)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),
    );
  }
}
