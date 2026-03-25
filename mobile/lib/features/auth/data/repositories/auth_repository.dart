import 'package:dio/dio.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../models/auth_response.dart';
import '../models/login_request.dart';
import '../models/otp_setup_response.dart';
import '../models/register_request.dart';
import '../models/user.dart';

class AuthRepository {
  final DioClient _dioClient;

  AuthRepository(this._dioClient);

  Future<AuthResponse> login(LoginRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        '${ApiEndpoints.login}?set_cookie=false',
        data: request.toJson(),
      );
      return AuthResponse.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<AuthResponse> register(RegisterRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        '${ApiEndpoints.register}?set_cookie=false',
        data: request.toJson(),
      );
      return AuthResponse.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> logout() async {
    try {
      await _dioClient.dio.post(ApiEndpoints.logout);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<User> getMe() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.me);
      return User.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<User> updateMe(Map<String, dynamic> data) async {
    try {
      final response = await _dioClient.dio.patch(ApiEndpoints.updateMe, data: data);
      return User.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<User> uploadAvatar(List<int> fileBytes, String fileName) async {
    try {
      final formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(fileBytes, filename: fileName),
      });
      final response = await _dioClient.dio.post(
        ApiEndpoints.avatar,
        data: formData,
      );
      return User.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<AuthResponse> refreshToken(String refreshToken) async {
    try {
      final response = await _dioClient.dio.post(
        '${ApiEndpoints.refresh}?set_cookie=false',
        data: {'refresh_token': refreshToken},
      );
      return AuthResponse.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
    required String confirmPassword,
  }) async {
    try {
      await _dioClient.dio.post(ApiEndpoints.changePassword, data: {
        'current_password': currentPassword,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      });
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> passwordResetRequest(String email) async {
    try {
      await _dioClient.dio.post(ApiEndpoints.passwordResetRequest, data: {'email': email});
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> passwordResetConfirm({
    required String token,
    required String newPassword,
    required String confirmPassword,
  }) async {
    try {
      await _dioClient.dio.post(ApiEndpoints.passwordResetConfirm, data: {
        'token': token,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      });
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<OtpSetupResponse> enableOtp() async {
    try {
      final response = await _dioClient.dio.post(ApiEndpoints.otpEnable);
      return OtpSetupResponse.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> confirmOtpSetup(String otpCode, String tempToken) async {
    try {
      await _dioClient.dio.post(ApiEndpoints.otpVerify, data: {
        'otp_code': otpCode,
        'temp_token': tempToken,
      });
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<AuthResponse> validateOtp(String otpCode, String tempToken) async {
    try {
      final response = await _dioClient.dio.post(
        '${ApiEndpoints.otpValidate}?set_cookie=false',
        data: {'otp_code': otpCode, 'temp_token': tempToken},
      );
      return AuthResponse.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> disableOtp(String password) async {
    try {
      await _dioClient.dio.post(ApiEndpoints.otpDisable, data: {'password': password});
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<String>> getEnabledSocialProviders() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.socialProviders);
      final data = response.data as Map<String, dynamic>;
      return List<String>.from(data['providers'] as List? ?? []);
    } catch (e) {
      return [];
    }
  }
}
