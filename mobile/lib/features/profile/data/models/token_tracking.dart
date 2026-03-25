enum TokenType {
  access,
  refresh,
  passwordReset,
  emailVerification,
  tempAuth,
  bearer;

  static TokenType fromString(String v) {
    switch (v) {
      case 'access':
        return TokenType.access;
      case 'refresh':
        return TokenType.refresh;
      case 'password_reset':
        return TokenType.passwordReset;
      case 'email_verification':
        return TokenType.emailVerification;
      case 'temp_auth':
        return TokenType.tempAuth;
      case 'bearer':
        return TokenType.bearer;
      default:
        return TokenType.access;
    }
  }

  String toJson() {
    switch (this) {
      case TokenType.access:
        return 'access';
      case TokenType.refresh:
        return 'refresh';
      case TokenType.passwordReset:
        return 'password_reset';
      case TokenType.emailVerification:
        return 'email_verification';
      case TokenType.tempAuth:
        return 'temp_auth';
      case TokenType.bearer:
        return 'bearer';
    }
  }
}

class TokenTracking {
  final String id;
  final String userId;
  final String tokenJti;
  final TokenType tokenType;
  final String ipAddress;
  final String userAgent;
  final bool isActive;
  final String? revokedAt;
  final String revokeReason;
  final String expiresAt;
  final String createdAt;

  const TokenTracking({
    required this.id,
    required this.userId,
    required this.tokenJti,
    required this.tokenType,
    required this.ipAddress,
    required this.userAgent,
    required this.isActive,
    this.revokedAt,
    required this.revokeReason,
    required this.expiresAt,
    required this.createdAt,
  });

  factory TokenTracking.fromJson(Map<String, dynamic> json) {
    return TokenTracking(
      id: json['id'].toString(),
      userId: json['user_id']?.toString() ?? '',
      tokenJti: json['token_jti'] as String? ?? '',
      tokenType: TokenType.fromString(json['token_type'] as String? ?? 'access'),
      ipAddress: json['ip_address'] as String? ?? '',
      userAgent: json['user_agent'] as String? ?? '',
      isActive: json['is_active'] as bool? ?? true,
      revokedAt: json['revoked_at'] as String?,
      revokeReason: json['revoke_reason'] as String? ?? '',
      expiresAt: json['expires_at'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}
