import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../storage/secure_storage.dart';

class DioClient {
  late final Dio _dio;
  final SecureStorage _secureStorage;
  bool _isRefreshing = false;

  DioClient(this._secureStorage) {
    final baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:8000/api/v1';
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {'Content-Type': 'application/json'},
      ),
    );
    _addInterceptors();
  }

  Dio get dio => _dio;

  void _addInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _secureStorage.getAccessToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401 && !_isRefreshing) {
            _isRefreshing = true;
            try {
              final refreshToken = await _secureStorage.getRefreshToken();
              if (refreshToken == null) {
                await _secureStorage.clearTokens();
                _isRefreshing = false;
                handler.next(error);
                return;
              }

              final response = await _dio.post(
                '/auth/refresh/?set_cookie=false',
                data: {'refresh_token': refreshToken},
                options: Options(
                  headers: {'Authorization': null},
                ),
              );

              final newAccessToken = response.data['access'] as String;
              final newRefreshToken = response.data['refresh'] as String?;
              await _secureStorage.saveAccessToken(newAccessToken);
              if (newRefreshToken != null) {
                await _secureStorage.saveRefreshToken(newRefreshToken);
              }

              _isRefreshing = false;

              // Retry original request
              final opts = error.requestOptions;
              opts.headers['Authorization'] = 'Bearer $newAccessToken';
              final retryResponse = await _dio.fetch(opts);
              handler.resolve(retryResponse);
            } catch (e) {
              _isRefreshing = false;
              await _secureStorage.clearTokens();
              handler.next(error);
            }
          } else {
            handler.next(error);
          }
        },
      ),
    );
  }
}
