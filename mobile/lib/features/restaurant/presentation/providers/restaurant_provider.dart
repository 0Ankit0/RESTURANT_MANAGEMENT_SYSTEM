import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/providers/dio_provider.dart';
import '../../data/models/restaurant_models.dart';
import '../../data/repositories/restaurant_repository.dart';

final restaurantRepositoryProvider = Provider<RestaurantRepository>((ref) {
  return RestaurantRepository(ref.watch(dioClientProvider));
});

final selectedBranchIdProvider = StateProvider<int>((ref) => 1);

final restaurantBranchesProvider = FutureProvider<List<RestaurantBranchItem>>((ref) {
  return ref.watch(restaurantRepositoryProvider).getBranches();
});

final restaurantTablesProvider = FutureProvider<List<RestaurantTableItem>>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getTables(branchId);
});

final restaurantOrdersProvider = FutureProvider<CursorPage<RestaurantOrderItem>>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getOrders(branchId);
});

final restaurantWaitlistProvider = FutureProvider<CursorPage<RestaurantWaitlistItem>>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getWaitlist(branchId);
});

final restaurantBranchReportProvider = FutureProvider<BranchOperationsReport>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getBranchReport(branchId);
});
