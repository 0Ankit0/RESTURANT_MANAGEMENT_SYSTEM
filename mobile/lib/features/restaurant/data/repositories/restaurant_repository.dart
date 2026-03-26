import '../../../../core/error/error_handler.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../models/restaurant_models.dart';

class RestaurantRepository {
  final DioClient _dioClient;

  RestaurantRepository(this._dioClient);

  Future<List<RestaurantBranchItem>> getBranches() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.restaurantBranches);
      final list = response.data as List<dynamic>? ?? [];
      return list
          .map((item) => RestaurantBranchItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<RestaurantTableItem>> getTables(int branchId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantTables(branchId),
      );
      final list = response.data as List<dynamic>? ?? [];
      return list
          .map((item) => RestaurantTableItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<CursorPage<RestaurantOrderItem>> getOrders(int branchId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantOrders,
        queryParameters: {'branch_id': branchId},
      );
      final data = response.data as Map<String, dynamic>;
      final items = (data['items'] as List<dynamic>? ?? [])
          .map((item) => RestaurantOrderItem.fromJson(item as Map<String, dynamic>))
          .toList();
      return CursorPage(items: items, nextCursor: data['next_cursor'] as int?);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<BranchOperationsReport> getBranchReport(int branchId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantBranchReport,
        queryParameters: {'branch_id': branchId},
      );
      return BranchOperationsReport.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }



  Future<CursorPage<RestaurantWaitlistItem>> getWaitlist(int branchId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantWaitlist,
        queryParameters: {'branch_id': branchId},
      );
      final data = response.data as Map<String, dynamic>;
      final items = (data['items'] as List<dynamic>? ?? [])
          .map((item) => RestaurantWaitlistItem.fromJson(item as Map<String, dynamic>))
          .toList();
      return CursorPage(items: items, nextCursor: data['next_cursor'] as int?);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> seatTable({
    required int tableId,
    required int partySize,
    int? reservationId,
  }) async {
    try {
      await _dioClient.dio.post(
        ApiEndpoints.restaurantSeatTable(tableId),
        data: {
          'party_size': partySize,
          if (reservationId != null) 'reservation_id': reservationId,
        },
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> promoteWaitlist({required int waitlistId, required int tableId}) async {
    try {
      await _dioClient.dio.patch(
        ApiEndpoints.restaurantPromoteWaitlist(waitlistId),
        queryParameters: {'table_id': tableId},
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> createReservation({
    required int branchId,
    required String guestName,
    required String guestPhone,
    required int partySize,
  }) async {
    try {
      await _dioClient.dio.post(
        ApiEndpoints.restaurantReservations,
        data: {
          'branch_id': branchId,
          'guest_name': guestName,
          'guest_phone': guestPhone,
          'party_size': partySize,
          'reservation_time': DateTime.now().add(const Duration(minutes: 30)).toUtc().toIso8601String(),
        },
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }
}
