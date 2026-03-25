"""Standard analytics event name constants.

Centralising event names here ensures consistency across the codebase and
makes it trivial to audit what is being tracked.
"""


class AuthEvents:
    SIGNED_UP = "user_signed_up"
    LOGGED_IN = "user_logged_in"
    LOGGED_IN_SOCIAL = "user_logged_in_social"
    LOGGED_OUT = "user_logged_out"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    EMAIL_VERIFIED = "email_verified"
    OTP_ENABLED = "otp_enabled"
    OTP_DISABLED = "otp_disabled"
    OTP_VALIDATED = "otp_validated"


class PaymentEvents:
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_STARTED = "subscription_started"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"


class TenantEvents:
    TENANT_CREATED = "tenant_created"
    TENANT_MEMBER_INVITED = "tenant_member_invited"
    TENANT_MEMBER_JOINED = "tenant_member_joined"
    TENANT_MEMBER_REMOVED = "tenant_member_removed"


class ApiEvents:
    REQUEST = "api_request"
    ERROR = "api_error"


class UserEvents:
    PROFILE_UPDATED = "profile_updated"
    AVATAR_UPLOADED = "avatar_uploaded"
    TOKEN_REVOKED = "token_revoked"
