import '../../../../core/error/error_handler.dart';
import '../../../../core/models/paginated_response.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../../../profile/data/models/token_tracking.dart';

class TokenRepository {
  final DioClient _dioClient;

  TokenRepository(this._dioClient);

  Future<PaginatedResponse<TokenTracking>> getTokens({
    int skip = 0,
    int limit = 20,
  }) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.tokens,
        queryParameters: {'skip': skip, 'limit': limit},
      );
      return PaginatedResponse.fromJson(
        response.data as Map<String, dynamic>,
        TokenTracking.fromJson,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> revokeToken(String tokenId) async {
    try {
      await _dioClient.dio.post(ApiEndpoints.revokeToken(tokenId));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> revokeAllTokens() async {
    try {
      await _dioClient.dio.post(ApiEndpoints.revokeAll);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }
}
