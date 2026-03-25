import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/loading_button.dart';
import '../providers/auth_provider.dart';

class OtpVerifyPage extends ConsumerStatefulWidget {
  final String tempToken;

  const OtpVerifyPage({super.key, required this.tempToken});

  @override
  ConsumerState<OtpVerifyPage> createState() => _OtpVerifyPageState();
}

class _OtpVerifyPageState extends ConsumerState<OtpVerifyPage> {
  final _formKey = GlobalKey<FormState>();
  final _otpController = TextEditingController();

  @override
  void dispose() {
    _otpController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    await ref
        .read(authNotifierProvider.notifier)
        .validateOtp(_otpController.text.trim(), widget.tempToken);
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final isLoading = authState.isLoading;

    ref.listen(authNotifierProvider, (prev, next) {
      final value = next.valueOrNull;
      if (value == null) return;
      if (value.error != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(value.error!), backgroundColor: Colors.red),
        );
        ref.read(authNotifierProvider.notifier).clearError();
      }
    });

    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: () => context.go(AppConstants.loginRoute)),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),
                Icon(
                  Icons.shield_outlined,
                  size: 72,
                  color: Theme.of(context).colorScheme.primary,
                ).animate().fadeIn(duration: 500.ms).scale(),
                const SizedBox(height: 24),
                Text(
                  'Two-Factor Authentication',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                  textAlign: TextAlign.center,
                ).animate().fadeIn(delay: 200.ms),
                const SizedBox(height: 8),
                Text(
                  'Enter the 6-digit code from your authenticator app',
                  style: Theme.of(context)
                      .textTheme
                      .bodyMedium
                      ?.copyWith(color: Colors.grey),
                  textAlign: TextAlign.center,
                ).animate().fadeIn(delay: 300.ms),
                const SizedBox(height: 40),
                AppTextField(
                  controller: _otpController,
                  label: 'OTP Code',
                  prefixIcon: Icons.pin_outlined,
                  keyboardType: TextInputType.number,
                  validator: (v) {
                    if (v == null || v.isEmpty) return 'Enter your OTP code';
                    if (v.length != 6) return 'OTP must be 6 digits';
                    return null;
                  },
                ).animate().fadeIn(delay: 400.ms).slideY(begin: 0.1),
                const SizedBox(height: 32),
                LoadingButton(
                  isLoading: isLoading,
                  onPressed: _submit,
                  label: 'Verify',
                  icon: Icons.verified_outlined,
                ).animate().fadeIn(delay: 500.ms),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () => context.go(AppConstants.loginRoute),
                  child: const Text('Back to Sign In'),
                ).animate().fadeIn(delay: 600.ms),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
