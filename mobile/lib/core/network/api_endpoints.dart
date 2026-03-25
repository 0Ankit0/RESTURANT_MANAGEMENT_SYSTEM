class ApiEndpoints {
  ApiEndpoints._();

  // Auth
  static const String login = '/auth/login/';
  static const String register = '/auth/signup/';
  static const String logout = '/auth/logout/';
  static const String refresh = '/auth/refresh/';
  static const String me = '/users/me';
  static const String updateMe = '/users/me';
  static const String avatar = '/users/me/avatar';
  static const String changePassword = '/auth/change-password/';
  static const String passwordResetRequest = '/auth/password-reset-request/';
  static const String passwordResetConfirm = '/auth/password-reset-confirm/';
  static const String resendVerification = '/auth/resend-verification/';

  // Social Auth
  static const String socialProviders = '/auth/social/providers/';
  static String socialLogin(String provider) => '/auth/social/$provider/';

  // OTP / 2FA
  static const String otpEnable = '/auth/otp/enable/';
  static const String otpVerify = '/auth/otp/verify/';
  static const String otpValidate = '/auth/otp/validate/';
  static const String otpDisable = '/auth/otp/disable/';

  // Notifications
  static const String notifications = '/notifications/';
  static String markNotificationRead(String id) => '/notifications/$id/read/';
  static String deleteNotification(String id) => '/notifications/$id/';
  static const String markAllNotificationsRead = '/notifications/read-all/';
  static const String notificationPreferences = '/notifications/preferences/';
  static const String notificationDevices = '/notifications/devices/';
  static String notificationDevicesByProvider(String provider) =>
      '/notifications/devices/$provider/';
  static const String notificationPushConfig = '/notifications/push/config/';
  static const String systemCapabilities = '/system/capabilities/';
  static const String systemProviders = '/system/providers/';
  static const String systemGeneralSettings = '/system/general-settings/';

  // IAM - Token tracking
  static const String tokens = '/tokens/';
  static String revokeToken(String id) => '/tokens/revoke/$id';
  static const String revokeAll = '/tokens/revoke-all';

  // Payments
  static const String payments = '/payments/';
  static const String paymentProviders = '/payments/providers/';
  static const String paymentInitiate = '/payments/initiate/';
  static const String paymentVerify = '/payments/verify/';
}
