class OtpSetupResponse {
  final String otpBase32;
  final String otpAuthUrl;
  final String qrCode;

  const OtpSetupResponse({
    required this.otpBase32,
    required this.otpAuthUrl,
    required this.qrCode,
  });

  factory OtpSetupResponse.fromJson(Map<String, dynamic> json) {
    return OtpSetupResponse(
      otpBase32: json['otp_base32'] as String? ?? '',
      otpAuthUrl: json['otp_auth_url'] as String? ?? '',
      qrCode: json['qr_code'] as String? ?? '',
    );
  }
}
