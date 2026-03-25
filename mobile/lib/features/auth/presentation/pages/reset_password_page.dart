import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/analytics/analytics_provider.dart';
import '../../../../core/analytics/analytics_events.dart';
import '../../../../shared/widgets/app_text_field.dart';
import '../../../../shared/widgets/loading_button.dart';

class ResetPasswordPage extends ConsumerStatefulWidget {
  final String token;

  const ResetPasswordPage({super.key, required this.token});

  @override
  ConsumerState<ResetPasswordPage> createState() => _ResetPasswordPageState();
}

class _ResetPasswordPageState extends ConsumerState<ResetPasswordPage> {
  final _formKey = GlobalKey<FormState>();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _isLoading = false;
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  bool _success = false;

  @override
  void dispose() {
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    try {
      final dio = ref.read(dioClientProvider).dio;
      await dio.post(ApiEndpoints.passwordResetConfirm, data: {
        'token': widget.token,
        'new_password': _newPasswordController.text,
        'confirm_password': _confirmPasswordController.text,
      });
      if (mounted) setState(() { _isLoading = false; _success = true; });
      ref.read(analyticsServiceProvider).capture(AuthAnalyticsEvents.passwordResetCompleted);
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
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
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: BackButton(onPressed: () => context.go(AppConstants.loginRoute)),
        title: const Text('Reset Password'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: _success
              ? Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.check_circle_outline,
                            size: 80, color: Colors.green)
                        .animate()
                        .scale(),
                    const SizedBox(height: 24),
                    Text('Password Reset Successful',
                        style: Theme.of(context).textTheme.headlineSmall,
                        textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    const Text(
                      'Your password has been updated. You can now sign in with your new password.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey),
                    ),
                    const SizedBox(height: 32),
                    ElevatedButton(
                      onPressed: () => context.go(AppConstants.loginRoute),
                      child: const Text('Sign In'),
                    ),
                  ],
                )
              : Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Set New Password',
                        style: Theme.of(context)
                            .textTheme
                            .headlineMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ).animate().fadeIn(),
                      const SizedBox(height: 8),
                      const Text(
                        'Enter and confirm your new password',
                        style: TextStyle(color: Colors.grey),
                      ).animate().fadeIn(delay: 100.ms),
                      const SizedBox(height: 32),
                      AppTextField(
                        controller: _newPasswordController,
                        label: 'New Password',
                        prefixIcon: Icons.lock_outline,
                        obscureText: _obscureNew,
                        suffixIcon: IconButton(
                          icon: Icon(_obscureNew
                              ? Icons.visibility_off_outlined
                              : Icons.visibility_outlined),
                          onPressed: () =>
                              setState(() => _obscureNew = !_obscureNew),
                        ),
                        validator: (v) {
                          if (v == null || v.isEmpty) return 'Enter new password';
                          if (v.length < 8) return 'Password must be at least 8 characters';
                          return null;
                        },
                      ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.1),
                      const SizedBox(height: 16),
                      AppTextField(
                        controller: _confirmPasswordController,
                        label: 'Confirm Password',
                        prefixIcon: Icons.lock_outline,
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
                          if (v != _newPasswordController.text) {
                            return 'Passwords do not match';
                          }
                          return null;
                        },
                      ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.1),
                      const SizedBox(height: 32),
                      LoadingButton(
                        isLoading: _isLoading,
                        onPressed: _submit,
                        label: 'Reset Password',
                      ).animate().fadeIn(delay: 400.ms),
                    ],
                  ),
                ),
        ),
      ),
    );
  }
}
