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

class ForgotPasswordPage extends ConsumerStatefulWidget {
  const ForgotPasswordPage({super.key});

  @override
  ConsumerState<ForgotPasswordPage> createState() => _ForgotPasswordPageState();
}

class _ForgotPasswordPageState extends ConsumerState<ForgotPasswordPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;
  bool _submitted = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    try {
      final dio = ref.read(dioClientProvider).dio;
      await dio.post(
        ApiEndpoints.passwordResetRequest,
        data: {'email': _emailController.text.trim()},
      );
      if (mounted) setState(() { _isLoading = false; _submitted = true; });
      ref.read(analyticsServiceProvider).capture(AuthAnalyticsEvents.passwordResetRequested);
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
        leading: BackButton(
          onPressed: () => context.go(AppConstants.loginRoute),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: _submitted
              ? Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.mark_email_read_outlined,
                        size: 80,
                        color: Theme.of(context).colorScheme.primary)
                        .animate()
                        .scale(),
                    const SizedBox(height: 24),
                    Text('Check your email',
                        style: Theme.of(context).textTheme.headlineSmall,
                        textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    Text(
                      'We\'ve sent a password reset link to ${_emailController.text}',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.grey),
                    ),
                    const SizedBox(height: 32),
                    TextButton(
                      onPressed: () => context.go(AppConstants.loginRoute),
                      child: const Text('Back to Sign In'),
                    ),
                  ],
                )
              : Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Forgot password?',
                        style: Theme.of(context)
                            .textTheme
                            .headlineMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ).animate().fadeIn(),
                      const SizedBox(height: 8),
                      const Text(
                        'Enter your email to reset your password',
                        style: TextStyle(color: Colors.grey),
                      ).animate().fadeIn(delay: 100.ms),
                      const SizedBox(height: 32),
                      AppTextField(
                        controller: _emailController,
                        label: 'Email',
                        prefixIcon: Icons.email_outlined,
                        keyboardType: TextInputType.emailAddress,
                        validator: (v) {
                          if (v == null || v.isEmpty) return 'Enter your email';
                          if (!v.contains('@')) return 'Enter a valid email';
                          return null;
                        },
                      ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.1),
                      const SizedBox(height: 32),
                      LoadingButton(
                        isLoading: _isLoading,
                        onPressed: _submit,
                        label: 'Send Reset Link',
                      ).animate().fadeIn(delay: 300.ms),
                    ],
                  ),
                ),
        ),
      ),
    );
  }
}
