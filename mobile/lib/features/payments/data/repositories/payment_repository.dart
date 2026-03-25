import '../../../../core/network/dio_client.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/error/error_handler.dart';
import '../models/payment.dart';

class PaymentRepository {
  final DioClient _dioClient;

  PaymentRepository(this._dioClient);

  Future<List<String>> getProviders() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.paymentProviders);
      final list = response.data as List<dynamic>? ?? [];
      return list.map((e) => e as String).toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<InitiatePaymentResponse> initiatePayment(InitiatePaymentRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.paymentInitiate,
        data: request.toJson(),
      );
      return InitiatePaymentResponse.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<VerifyPaymentResponse> verifyPayment(VerifyPaymentRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.paymentVerify,
        data: request.toJson(),
      );
      return VerifyPaymentResponse.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<PaymentTransaction>> getTransactions() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.payments);
      final list = response.data as List<dynamic>? ?? [];
      return list
          .map((e) => PaymentTransaction.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<PaymentTransaction> getTransaction(int transactionId) async {
    try {
      final response = await _dioClient.dio.get('${ApiEndpoints.payments}$transactionId/');
      return PaymentTransaction.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }
}
