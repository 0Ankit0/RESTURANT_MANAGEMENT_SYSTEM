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

  Future<List<RestaurantReservationItem>> getReservations(int branchId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantReservations,
        queryParameters: {'branch_id': branchId},
      );
      final list = response.data as List<dynamic>? ?? [];
      return list
          .map((item) => RestaurantReservationItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<CursorPage<KitchenTicketItem>> getKitchenTickets({int? branchId}) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantKitchenTickets,
        queryParameters: {if (branchId != null) 'branch_id': branchId},
      );
      final data = response.data as Map<String, dynamic>;
      final items = (data['items'] as List<dynamic>? ?? [])
          .map((item) => KitchenTicketItem.fromJson(item as Map<String, dynamic>))
          .toList();
      return CursorPage(items: items, nextCursor: data['next_cursor'] as int?);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<KitchenTicketItem> updateKitchenTicket({
    required int ticketId,
    required String status,
    int? updatedBy,
  }) async {
    try {
      final response = await _dioClient.dio.patch(
        ApiEndpoints.restaurantKitchenTicket(ticketId),
        data: {
          'status': status,
          if (updatedBy != null) 'updated_by': updatedBy,
        },
      );
      return KitchenTicketItem.fromJson(response.data as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<StockAlertItem>> getStockAlerts(int branchId, {int limit = 20}) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantStockAlerts,
        queryParameters: {'branch_id': branchId, 'limit': limit},
      );
      final data = response.data;
      final items = data is Map<String, dynamic>
          ? (data['items'] as List<dynamic>? ?? [])
          : (data as List<dynamic>? ?? []);
      return items
          .map((item) => StockAlertItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<OperationalNotificationItem>> getOperationalNotifications(
    int branchId, {
    int limit = 20,
  }) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantOperationalNotifications,
        queryParameters: {'branch_id': branchId, 'limit': limit},
      );
      final list = response.data as List<dynamic>? ?? [];
      return list
          .map((item) => OperationalNotificationItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<RestaurantBillItem>> getBills(int branchId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantBills,
        queryParameters: {'branch_id': branchId},
      );
      final list = response.data as List<dynamic>? ?? [];
      return list
          .map((item) => RestaurantBillItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> settleBill({
    required int billId,
    required double amount,
    required String paymentMethod,
    int? cashierId,
  }) async {
    try {
      await _dioClient.dio.post(
        ApiEndpoints.restaurantBillSettlements(billId),
        data: {
          if (cashierId != null) 'cashier_id': cashierId,
          'settlements': [
            {'payment_method': paymentMethod, 'amount': amount},
          ],
        },
      );
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
          'reservation_time': DateTime.now()
              .add(const Duration(minutes: 30))
              .toUtc()
              .toIso8601String(),
        },
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> transitionReservation({
    required int reservationId,
    required String status,
  }) async {
    try {
      if (status == 'cancelled') {
        await _dioClient.dio.post(
          ApiEndpoints.restaurantReservationCancel(reservationId),
        );
        return;
      }
      await _dioClient.dio.patch(
        ApiEndpoints.restaurantReservation(reservationId),
        data: {'status': status},
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> updateOrderStatus({
    required int orderId,
    required String status,
  }) async {
    try {
      await _dioClient.dio.patch(
        ApiEndpoints.restaurantOrder(orderId),
        data: {'status': status},
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<DayCloseItem?> getLatestOpenDayClose(int branchId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantDayClose,
        queryParameters: {'branch_id': branchId, 'status_filter': 'open', 'limit': 1},
      );
      final data = response.data as Map<String, dynamic>? ?? {};
      final items = data['items'] as List<dynamic>? ?? [];
      if (items.isEmpty) return null;
      return DayCloseItem.fromJson(items.first as Map<String, dynamic>);
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<DayCloseBlockerItem>> getDayCloseBlockers(int dayCloseId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.restaurantDayCloseBlockers(dayCloseId),
      );
      final data = response.data as Map<String, dynamic>? ?? {};
      final items = data['blockers'] as List<dynamic>? ?? [];
      return items
          .map((item) => DayCloseBlockerItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> acknowledgeStaffingGap({
    required int dayCloseId,
    required int acknowledgedBy,
  }) async {
    try {
      await _dioClient.dio.post(
        ApiEndpoints.restaurantAcknowledgeStaffingGap(dayCloseId),
        data: {'acknowledged_by': acknowledgedBy},
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }
}
