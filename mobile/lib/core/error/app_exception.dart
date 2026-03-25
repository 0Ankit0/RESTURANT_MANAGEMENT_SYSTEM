class AppException implements Exception {
  final String message;
  final int? statusCode;

  const AppException({required this.message, this.statusCode});

  @override
  String toString() => 'AppException: $message (status: $statusCode)';
}

class NetworkException extends AppException {
  const NetworkException({required super.message, super.statusCode});
}

class AuthException extends AppException {
  const AuthException({required super.message, super.statusCode});
}

class UnauthorizedException extends AuthException {
  const UnauthorizedException()
      : super(message: 'Unauthorized. Please log in again.', statusCode: 401);
}

class ServerException extends AppException {
  const ServerException({required super.message, super.statusCode});
}
