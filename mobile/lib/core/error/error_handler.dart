import 'package:dio/dio.dart';
import 'app_exception.dart';

class ErrorHandler {
  static AppException handle(dynamic error) {
    if (error is DioException) {
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
        case DioExceptionType.sendTimeout:
        case DioExceptionType.receiveTimeout:
          return const NetworkException(message: 'Connection timed out.');
        case DioExceptionType.badResponse:
          final statusCode = error.response?.statusCode;
          final data = error.response?.data;
          String message = 'An error occurred.';
          if (data is Map) {
            message = data['detail']?.toString() ??
                data['message']?.toString() ??
                message;
          }
          if (statusCode == 401) {
            return const UnauthorizedException();
          }
          return ServerException(message: message, statusCode: statusCode);
        case DioExceptionType.connectionError:
          return const NetworkException(
              message: 'No internet connection. Please check your network.');
        default:
          return AppException(message: error.message ?? 'Unknown error.');
      }
    }
    if (error is AppException) return error;
    return AppException(message: error.toString());
  }
}
