import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../data/models/payment.dart';
import '../../data/repositories/payment_repository.dart';

final paymentRepositoryProvider = Provider<PaymentRepository>((ref) {
  return PaymentRepository(ref.watch(dioClientProvider));
});

final paymentProvidersProvider = FutureProvider<List<String>>((ref) {
  return ref.watch(paymentRepositoryProvider).getProviders();
});

final transactionsProvider = FutureProvider<List<PaymentTransaction>>((ref) {
  return ref.watch(paymentRepositoryProvider).getTransactions();
});
