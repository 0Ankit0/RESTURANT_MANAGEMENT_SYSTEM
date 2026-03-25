/** Standard analytics event name constants — keeps tracking calls consistent. */

export const AuthEvents = {
  SIGNED_UP: 'user_signed_up',
  LOGGED_IN: 'user_logged_in',
  LOGGED_IN_SOCIAL: 'user_logged_in_social',
  LOGGED_OUT: 'user_logged_out',
  PASSWORD_CHANGED: 'password_changed',
  PASSWORD_RESET_REQUESTED: 'password_reset_requested',
  PASSWORD_RESET_COMPLETED: 'password_reset_completed',
  EMAIL_VERIFIED: 'email_verified',
  OTP_ENABLED: 'otp_enabled',
  OTP_DISABLED: 'otp_disabled',
} as const;

export const NavigationEvents = {
  PAGE_VIEW: '$pageview',
  SCREEN_VIEW: 'screen_view',
} as const;

export const PaymentEvents = {
  PAYMENT_INITIATED: 'payment_initiated',
  PAYMENT_COMPLETED: 'payment_completed',
  PAYMENT_FAILED: 'payment_failed',
} as const;

export const UserEvents = {
  PROFILE_UPDATED: 'profile_updated',
  AVATAR_UPLOADED: 'avatar_uploaded',
  TOKEN_REVOKED: 'token_revoked',
} as const;

export const TenantEvents = {
  TENANT_CREATED: 'tenant_created',
  TENANT_MEMBER_INVITED: 'tenant_member_invited',
  TENANT_MEMBER_JOINED: 'tenant_member_joined',
} as const;
