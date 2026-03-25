class AuthResponse {
  final String? access;
  final String? refresh;
  final String tokenType;
  final bool requiresOtp;
  final String? tempToken;

  const AuthResponse({
    this.access,
    this.refresh,
    this.tokenType = 'bearer',
    this.requiresOtp = false,
    this.tempToken,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      access: json['access'] as String?,
      refresh: json['refresh'] as String?,
      tokenType: json['token_type'] as String? ?? 'bearer',
      requiresOtp: json['requires_otp'] as bool? ?? false,
      tempToken: json['temp_token'] as String?,
    );
  }
}
