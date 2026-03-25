import 'dart:convert';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/analytics/analytics_provider.dart';
import '../../../../core/analytics/analytics_events.dart';
import '../../../../features/auth/data/models/otp_setup_response.dart';
import '../../../../features/auth/data/models/user.dart';
import '../../../../features/auth/presentation/providers/auth_provider.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/loading_button.dart';

class ProfilePage extends ConsumerStatefulWidget {
  const ProfilePage({super.key});

  @override
  ConsumerState<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends ConsumerState<ProfilePage> {
  // Personal Info
  final _infoFormKey = GlobalKey<FormState>();
  late TextEditingController _firstNameController;
  late TextEditingController _lastNameController;
  late TextEditingController _phoneController;
  bool _savingInfo = false;

  // Change Password
  final _pwFormKey = GlobalKey<FormState>();
  final _currentPwController = TextEditingController();
  final _newPwController = TextEditingController();
  final _confirmPwController = TextEditingController();
  bool _savingPw = false;
  bool _obscureCurrent = true;
  bool _obscureNew = true;
  bool _obscureConfirm = true;

  // 2FA
  bool _otpLoading = false;
  OtpSetupResponse? _otpSetupResult;
  final _otpConfirmController = TextEditingController();
  bool _confirmingOtp = false;
  // Disable OTP
  final _disablePwController = TextEditingController();

  @override
  void initState() {
    super.initState();
    final user = ref.read(authNotifierProvider).valueOrNull?.user;
    _firstNameController =
        TextEditingController(text: user?.firstName ?? '');
    _lastNameController =
        TextEditingController(text: user?.lastName ?? '');
    _phoneController = TextEditingController(text: user?.phone ?? '');
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _phoneController.dispose();
    _currentPwController.dispose();
    _newPwController.dispose();
    _confirmPwController.dispose();
    _otpConfirmController.dispose();
    _disablePwController.dispose();
    super.dispose();
  }

  void _showSnack(String message, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: error ? Colors.red : Colors.green,
      ),
    );
  }

  Future<void> _savePersonalInfo() async {
    if (!_infoFormKey.currentState!.validate()) return;
    setState(() => _savingInfo = true);
    try {
      final repo = ref.read(authRepositoryProvider);
      final updated = await repo.updateMe({
        'first_name': _firstNameController.text.trim(),
        'last_name': _lastNameController.text.trim(),
        'phone': _phoneController.text.trim(),
      });
      ref.read(authNotifierProvider.notifier).updateUser(updated);
      ref.read(analyticsServiceProvider).capture(UserAnalyticsEvents.profileUpdated);
      _showSnack('Profile updated successfully');
    } catch (e) {
      _showSnack(ErrorHandler.handle(e).message, error: true);
    } finally {
      if (mounted) setState(() => _savingInfo = false);
    }
  }

  Future<void> _changePassword() async {
    if (!_pwFormKey.currentState!.validate()) return;
    setState(() => _savingPw = true);
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.changePassword(
        currentPassword: _currentPwController.text,
        newPassword: _newPwController.text,
        confirmPassword: _confirmPwController.text,
      );
      _currentPwController.clear();
      _newPwController.clear();
      _confirmPwController.clear();
      _showSnack('Password changed successfully');
      ref.read(analyticsServiceProvider).capture(AuthAnalyticsEvents.passwordChanged);
    } catch (e) {
      _showSnack(ErrorHandler.handle(e).message, error: true);
    } finally {
      if (mounted) setState(() => _savingPw = false);
    }
  }

  Future<void> _enableOtp() async {
    setState(() => _otpLoading = true);
    try {
      final repo = ref.read(authRepositoryProvider);
      final result = await repo.enableOtp();
      setState(() => _otpSetupResult = result);
    } catch (e) {
      _showSnack(ErrorHandler.handle(e).message, error: true);
    } finally {
      if (mounted) setState(() => _otpLoading = false);
    }
  }

  Future<void> _confirmOtpSetup() async {
    if (_otpConfirmController.text.length != 6) {
      _showSnack('Enter the 6-digit OTP code', error: true);
      return;
    }
    setState(() => _confirmingOtp = true);
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.confirmOtpSetup(
          _otpConfirmController.text, _otpSetupResult!.otpBase32);
      // Refresh user
      final updated = await repo.getMe();
      ref.read(authNotifierProvider.notifier).updateUser(updated);
      setState(() => _otpSetupResult = null);
      _otpConfirmController.clear();
      ref.read(analyticsServiceProvider).capture(AuthAnalyticsEvents.otpEnabled);
      _showSnack('Two-factor authentication enabled!');
    } catch (e) {
      _showSnack(ErrorHandler.handle(e).message, error: true);
    } finally {
      if (mounted) setState(() => _confirmingOtp = false);
    }
  }

  Future<void> _disableOtp() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Disable 2FA'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
                'Enter your password to confirm disabling two-factor authentication.'),
            const SizedBox(height: 16),
            TextField(
              controller: _disablePwController,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Password',
                prefixIcon: Icon(Icons.lock_outline),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () {
                _disablePwController.clear();
                Navigator.pop(ctx, false);
              },
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Disable',
                  style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (confirm != true) return;

    setState(() => _otpLoading = true);
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.disableOtp(_disablePwController.text);
      _disablePwController.clear();
      final updated = await repo.getMe();
      ref.read(authNotifierProvider.notifier).updateUser(updated);
      ref.read(analyticsServiceProvider).capture(AuthAnalyticsEvents.otpDisabled);
      _showSnack('Two-factor authentication disabled');
    } catch (e) {
      _showSnack(ErrorHandler.handle(e).message, error: true);
    } finally {
      if (mounted) setState(() => _otpLoading = false);
    }
  }

  Future<void> _showAvatarUploadDialog(User user) async {
    final urlController =
        TextEditingController(text: user.imageUrl ?? '');
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Upload Avatar'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Avatar upload requires selecting a file. Enter an image URL to preview, or use the REST API to upload a file directly.',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: urlController,
              decoration: const InputDecoration(
                labelText: 'Image URL (optional)',
                prefixIcon: Icon(Icons.link_outlined),
              ),
              keyboardType: TextInputType.url,
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Update')),
        ],
      ),
    );
    if (confirmed == true && urlController.text.trim().isNotEmpty) {
      try {
        final repo = ref.read(authRepositoryProvider);
        final updated =
            await repo.updateMe({'image_url': urlController.text.trim()});
        ref.read(authNotifierProvider.notifier).updateUser(updated);
        ref.read(analyticsServiceProvider).capture(UserAnalyticsEvents.avatarUploaded);
        _showSnack('Avatar updated');
      } catch (e) {
        _showSnack(ErrorHandler.handle(e).message, error: true);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final user = authState.valueOrNull?.user;

    if (user == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await ref.read(authNotifierProvider.notifier).logout();
            },
            tooltip: 'Logout',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Avatar ──────────────────────────────────────────
            _buildAvatarSection(context, user),
            const SizedBox(height: 16),

            // ── Personal Info ──────────────────────────────────
            _buildPersonalInfoSection(context).animate().fadeIn(delay: 150.ms).slideY(begin: 0.05),
            const SizedBox(height: 12),

            // ── Change Password ────────────────────────────────
            _buildChangePasswordSection(context).animate().fadeIn(delay: 200.ms).slideY(begin: 0.05),
            const SizedBox(height: 12),

            // ── 2FA ───────────────────────────────────────────
            _buildTwoFactorSection(context, user).animate().fadeIn(delay: 250.ms).slideY(begin: 0.05),
            const SizedBox(height: 12),

            // ── Account Info ───────────────────────────────────
            _buildAccountInfoSection(context, user).animate().fadeIn(delay: 300.ms).slideY(begin: 0.05),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildAvatarSection(BuildContext context, User user) {
    return Center(
      child: Column(
        children: [
          Stack(
            children: [
              CircleAvatar(
                radius: 52,
                backgroundColor:
                    Theme.of(context).colorScheme.primaryContainer,
                child: user.imageUrl != null && user.imageUrl!.isNotEmpty
                    ? ClipOval(
                        child: CachedNetworkImage(
                          imageUrl: user.imageUrl!,
                          width: 104,
                          height: 104,
                          fit: BoxFit.cover,
                          placeholder: (_, __) =>
                              const CircularProgressIndicator(),
                          errorWidget: (_, __, ___) => Text(
                            user.initials,
                            style: Theme.of(context)
                                .textTheme
                                .headlineLarge
                                ?.copyWith(
                                  color: Theme.of(context)
                                      .colorScheme
                                      .onPrimaryContainer,
                                ),
                          ),
                        ),
                      )
                    : Text(
                        user.initials,
                        style: Theme.of(context)
                            .textTheme
                            .headlineLarge
                            ?.copyWith(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onPrimaryContainer,
                            ),
                      ),
              ),
              Positioned(
                bottom: 0,
                right: 0,
                child: GestureDetector(
                  onTap: () => _showAvatarUploadDialog(user),
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary,
                      shape: BoxShape.circle,
                      border: Border.all(
                          color: Theme.of(context).colorScheme.surface,
                          width: 2),
                    ),
                    child: const Icon(Icons.camera_alt_outlined,
                        size: 16, color: Colors.white),
                  ),
                ),
              ),
            ],
          ).animate().scale(delay: 50.ms),
          const SizedBox(height: 8),
          Text(
            user.displayName,
            style: Theme.of(context)
                .textTheme
                .titleLarge
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          Text(
            '@${user.username}',
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildPersonalInfoSection(BuildContext context) {
    return _SectionCard(
      title: 'Personal Information',
      icon: Icons.person_outline,
      child: Form(
        key: _infoFormKey,
        child: Column(
          children: [
            AppTextField(
              controller: _firstNameController,
              label: 'First Name',
              prefixIcon: Icons.badge_outlined,
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _lastNameController,
              label: 'Last Name',
              prefixIcon: Icons.badge_outlined,
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _phoneController,
              label: 'Phone',
              prefixIcon: Icons.phone_outlined,
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: LoadingButton(
                isLoading: _savingInfo,
                onPressed: _savePersonalInfo,
                label: 'Update Profile',
                icon: Icons.save_outlined,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChangePasswordSection(BuildContext context) {
    return _SectionCard(
      title: 'Change Password',
      icon: Icons.lock_outline,
      child: Form(
        key: _pwFormKey,
        child: Column(
          children: [
            AppTextField(
              controller: _currentPwController,
              label: 'Current Password',
              prefixIcon: Icons.lock_outline,
              obscureText: _obscureCurrent,
              suffixIcon: IconButton(
                icon: Icon(_obscureCurrent
                    ? Icons.visibility_off_outlined
                    : Icons.visibility_outlined),
                onPressed: () =>
                    setState(() => _obscureCurrent = !_obscureCurrent),
              ),
              validator: (v) =>
                  v == null || v.isEmpty ? 'Enter current password' : null,
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _newPwController,
              label: 'New Password',
              prefixIcon: Icons.lock_reset_outlined,
              obscureText: _obscureNew,
              suffixIcon: IconButton(
                icon: Icon(_obscureNew
                    ? Icons.visibility_off_outlined
                    : Icons.visibility_outlined),
                onPressed: () => setState(() => _obscureNew = !_obscureNew),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Enter new password';
                if (v.length < 8) return 'Min. 8 characters';
                return null;
              },
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _confirmPwController,
              label: 'Confirm Password',
              prefixIcon: Icons.lock_reset_outlined,
              obscureText: _obscureConfirm,
              suffixIcon: IconButton(
                icon: Icon(_obscureConfirm
                    ? Icons.visibility_off_outlined
                    : Icons.visibility_outlined),
                onPressed: () =>
                    setState(() => _obscureConfirm = !_obscureConfirm),
              ),
              validator: (v) {
                if (v == null || v.isEmpty) return 'Confirm your password';
                if (v != _newPwController.text) return 'Passwords do not match';
                return null;
              },
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: LoadingButton(
                isLoading: _savingPw,
                onPressed: _changePassword,
                label: 'Change Password',
                icon: Icons.lock_open_outlined,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTwoFactorSection(BuildContext context, User user) {
    final isEnabled = user.otpEnabled;

    return _SectionCard(
      title: 'Two-Factor Authentication',
      icon: Icons.shield_outlined,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isEnabled ? Icons.verified_user_outlined : Icons.security_outlined,
                color: isEnabled ? Colors.green : Colors.grey,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                isEnabled ? '2FA is Enabled' : '2FA is Disabled',
                style: TextStyle(
                  color: isEnabled ? Colors.green : Colors.grey,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (!isEnabled && _otpSetupResult == null) ...[
            const Text(
              'Add an extra layer of security to your account using an authenticator app.',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: LoadingButton(
                isLoading: _otpLoading,
                onPressed: _enableOtp,
                label: 'Enable 2FA',
                icon: Icons.shield_outlined,
              ),
            ),
          ] else if (_otpSetupResult != null) ...[
            const Text(
              'Scan the QR code with your authenticator app, then enter the 6-digit code to confirm.',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 16),
            Center(
              child: Container(
                decoration: BoxDecoration(
                  border: Border.all(
                      color: Theme.of(context).colorScheme.outline),
                  borderRadius: BorderRadius.circular(8),
                ),
                padding: const EdgeInsets.all(8),
                child: () {
                  try {
                    // Strip data URI prefix if present
                    String qr = _otpSetupResult!.qrCode;
                    if (qr.contains(',')) qr = qr.split(',').last;
                    return Image.memory(base64Decode(qr),
                        width: 200, height: 200);
                  } catch (_) {
                    return const Icon(Icons.qr_code, size: 200,
                        color: Colors.grey);
                  }
                }(),
              ),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context)
                    .colorScheme
                    .surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Manual entry key:',
                      style: TextStyle(fontSize: 12, color: Colors.grey)),
                  const SizedBox(height: 4),
                  SelectableText(
                    _otpSetupResult!.otpBase32,
                    style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 13,
                        fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            AppTextField(
              controller: _otpConfirmController,
              label: '6-Digit OTP Code',
              prefixIcon: Icons.pin_outlined,
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => setState(() => _otpSetupResult = null),
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: LoadingButton(
                    isLoading: _confirmingOtp,
                    onPressed: _confirmOtpSetup,
                    label: 'Confirm',
                    icon: Icons.check_outlined,
                  ),
                ),
              ],
            ),
          ] else ...[
            const Text(
              'Your account is protected with two-factor authentication.',
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _otpLoading ? null : _disableOtp,
                icon: _otpLoading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.shield_outlined,
                        color: Colors.red, size: 18),
                label: const Text('Disable 2FA',
                    style: TextStyle(color: Colors.red)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Colors.red),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAccountInfoSection(BuildContext context, User user) {
    return _SectionCard(
      title: 'Account Information',
      icon: Icons.info_outline,
      child: Column(
        children: [
          _InfoRow(label: 'Username', value: user.username),
          const SizedBox(height: 8),
          _InfoRow(label: 'Email', value: user.email),
          const SizedBox(height: 8),
          Row(
            children: [
              const SizedBox(
                width: 110,
                child: Text('Status',
                    style: TextStyle(color: Colors.grey, fontSize: 13)),
              ),
              _StatusBadge(
                label: user.isActive ? 'Active' : 'Inactive',
                color: user.isActive ? Colors.green : Colors.orange,
              ),
              const SizedBox(width: 8),
              _StatusBadge(
                label: user.isConfirmed ? 'Confirmed' : 'Unconfirmed',
                color:
                    user.isConfirmed ? Colors.blue : Colors.orange,
              ),
            ],
          ),
          if (user.isSuperuser) ...[
            const SizedBox(height: 8),
            const Row(
              children: [
                SizedBox(
                  width: 110,
                  child: Text('Role',
                      style: TextStyle(color: Colors.grey, fontSize: 13)),
                ),
                _StatusBadge(label: 'Superuser', color: Colors.purple),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

// ─── Reusable Widgets ──────────────────────────────────────────────────────────

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Widget child;

  const _SectionCard({
    required this.title,
    required this.icon,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon,
                    size: 18,
                    color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ],
            ),
            const Divider(height: 24),
            child,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 110,
          child: Text(label,
              style: const TextStyle(color: Colors.grey, fontSize: 13)),
        ),
        Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500))),
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
        style: TextStyle(
            color: color, fontWeight: FontWeight.bold, fontSize: 12),
      ),
    );
  }
}

