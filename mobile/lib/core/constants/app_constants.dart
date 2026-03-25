class AppConstants {
  AppConstants._();

  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';

  // Route names
  static const String loginRoute = '/login';
  static const String registerRoute = '/register';
  static const String forgotPasswordRoute = '/forgot-password';
  static const String otpVerifyRoute = '/otp-verify';
  static const String resetPasswordRoute = '/reset-password';
  static const String homeRoute = '/home';
  static const String notificationsRoute = '/home/notifications';
  static const String settingsRoute = '/home/settings';
  static const String profileRoute = '/home/profile';
  static const String tokensRoute = '/home/settings/tokens';
  static const String paymentsRoute = '/home/payments';

  // Social auth — the backend redirects here after OAuth; the WebView intercepts it
  static const String socialAuthCallbackPrefix = '/auth-callback';
}
