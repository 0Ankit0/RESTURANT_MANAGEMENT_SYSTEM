/// Standard analytics event name constants.
///
/// Centralising event names ensures consistency across the codebase.
class AuthAnalyticsEvents {
  AuthAnalyticsEvents._();

  static const String signedUp = 'user_signed_up';
  static const String loggedIn = 'user_logged_in';
  static const String loggedInSocial = 'user_logged_in_social';
  static const String loggedOut = 'user_logged_out';
  static const String passwordChanged = 'password_changed';
  static const String passwordResetRequested = 'password_reset_requested';
  static const String passwordResetCompleted = 'password_reset_completed';
  static const String otpEnabled = 'otp_enabled';
  static const String otpDisabled = 'otp_disabled';
  static const String otpValidated = 'otp_validated';
}

class NavigationAnalyticsEvents {
  NavigationAnalyticsEvents._();

  static const String screenView = 'screen_view';
}

class PaymentAnalyticsEvents {
  PaymentAnalyticsEvents._();

  static const String paymentInitiated = 'payment_initiated';
  static const String paymentCompleted = 'payment_completed';
  static const String paymentFailed = 'payment_failed';
}

class UserAnalyticsEvents {
  UserAnalyticsEvents._();

  static const String profileUpdated = 'profile_updated';
  static const String avatarUploaded = 'avatar_uploaded';
  static const String tokenRevoked = 'token_revoked';
}

class TenantAnalyticsEvents {
  TenantAnalyticsEvents._();

  static const String tenantCreated = 'tenant_created';
  static const String memberInvited = 'tenant_member_invited';
  static const String memberJoined = 'tenant_member_joined';
}
