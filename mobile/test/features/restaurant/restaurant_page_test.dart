import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile/core/analytics/analytics_interface.dart';
import 'package:mobile/core/analytics/analytics_provider.dart';
import 'package:mobile/core/analytics/analytics_service.dart';
import 'package:mobile/core/error/app_exception.dart';
import 'package:mobile/core/network/dio_client.dart';
import 'package:mobile/core/storage/secure_storage.dart';
import 'package:mobile/features/restaurant/data/models/restaurant_models.dart';
import 'package:mobile/features/restaurant/data/repositories/restaurant_repository.dart';
import 'package:mobile/features/restaurant/presentation/pages/restaurant_page.dart';
import 'package:mobile/features/restaurant/presentation/providers/restaurant_provider.dart';

class _MemoryAnalyticsAdapter implements AnalyticsAdapter {
  final List<String> events = [];

  @override
  Future<void> capture(String event, [Map<String, Object>? properties]) async {
    events.add(event);
  }

  @override
  Future<Map<String, Object>> getAllFeatureFlags() async => {};

  @override
  Future<void> group(String groupType, String groupKey, [Map<String, Object>? properties]) async {}

  @override
  Future<void> identify(String userId, [Map<String, Object>? properties]) async {}

  @override
  Future<bool> isFeatureFlagEnabled(String flagKey, {bool defaultValue = false}) async => defaultValue;

  @override
  Future<void> flush() async {}

  @override
  Future<void> reset() async {}

  @override
  Future<void> screen(String screenName, [Map<String, Object>? properties]) async {}

  @override
  Future<void> shutdown() async {}
}

class _FakeRestaurantRepository extends RestaurantRepository {
  _FakeRestaurantRepository() : super(DioClient(SecureStorage()));

  bool shouldFailSeat = false;

  @override
  Future<List<RestaurantBranchItem>> getBranches() async => [
        RestaurantBranchItem(id: 1, name: 'Downtown'),
        RestaurantBranchItem(id: 2, name: 'Airport'),
      ];

  @override
  Future<List<RestaurantTableItem>> getTables(int branchId) async {
    if (branchId == 1) {
      return [
        RestaurantTableItem(id: 11, code: 'D-1', status: 'available', seats: 4),
      ];
    }
    return [
      RestaurantTableItem(id: 21, code: 'A-1', status: 'occupied', seats: 2),
    ];
  }

  @override
  Future<CursorPage<RestaurantOrderItem>> getOrders(int branchId) async =>
      CursorPage(items: [RestaurantOrderItem(id: branchId * 100, status: 'submitted')], nextCursor: null);

  @override
  Future<CursorPage<RestaurantWaitlistItem>> getWaitlist(int branchId) async => CursorPage(
        items: [RestaurantWaitlistItem(id: branchId, guestName: 'Guest $branchId', partySize: 2, status: 'waiting')],
        nextCursor: null,
      );

  @override
  Future<BranchOperationsReport> getBranchReport(int branchId) async => BranchOperationsReport(
        branchId: branchId,
        ordersCount: branchId,
        openTickets: 1,
        grossSales: 25,
        collectedSales: 10,
        lowStockCount: 0,
        settlementHealth: SettlementHealth.empty(),
      );

  @override
  Future<CursorPage<KitchenTicketItem>> getKitchenTickets({int? branchId}) async => CursorPage(
        items: [
          KitchenTicketItem(
            id: 901,
            station: 'grill',
            status: 'queued',
            priority: 1,
            updatedAt: DateTime.now(),
          ),
        ],
        nextCursor: null,
      );

  @override
  Future<List<StockAlertItem>> getStockAlerts(int branchId, {int limit = 20}) async => [
        StockAlertItem(id: 1, branchId: branchId, itemName: 'Tomatoes', severity: 'warning', availableUnits: 4),
      ];

  @override
  Future<List<OperationalNotificationItem>> getOperationalNotifications(int branchId, {int limit = 20}) async => [
        OperationalNotificationItem(
          id: 1,
          branchId: branchId,
          eventName: 'Drawer opened',
          severity: 'info',
          occurredAt: DateTime.now(),
        ),
      ];

  @override
  Future<List<RestaurantBillItem>> getBills(int branchId) async => [
        RestaurantBillItem(id: 1, totalAmount: 20, paidAmount: 0, status: 'open'),
      ];

  @override
  Future<void> createReservation({required int branchId, required String guestName, required String guestPhone, required int partySize}) async {}

  @override
  Future<void> seatTable({required int tableId, required int partySize, int? reservationId}) async {
    if (shouldFailSeat) {
      throw const ServerException(message: 'Seat failed', statusCode: 500);
    }
  }

  @override
  Future<void> promoteWaitlist({required int waitlistId, required int tableId}) async {}

  @override
  Future<KitchenTicketItem> updateKitchenTicket({required int ticketId, required String status, int? updatedBy}) async =>
      KitchenTicketItem(id: ticketId, station: 'grill', status: status, priority: 1, updatedAt: DateTime.now());

  @override
  Future<void> settleBill({required int billId, required double amount, required String paymentMethod, int? cashierId}) async {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('switching branch updates branch-scoped data', (tester) async {
    final fakeRepo = _FakeRestaurantRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          restaurantRepositoryProvider.overrideWithValue(fakeRepo),
        ],
        child: const MaterialApp(home: RestaurantPage()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('D-1'), findsOneWidget);
    await tester.tap(find.byType(DropdownButton<int>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Airport (#2)').last);
    await tester.pumpAndSettle();

    expect(find.text('A-1'), findsOneWidget);
    expect(find.text('D-1'), findsNothing);
  });

  testWidgets('service actions emit success and failure analytics with retry', (tester) async {
    final fakeRepo = _FakeRestaurantRepository()..shouldFailSeat = true;
    final adapter = _MemoryAnalyticsAdapter();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          restaurantRepositoryProvider.overrideWithValue(fakeRepo),
          analyticsServiceProvider.overrideWithValue(AnalyticsService(adapter)),
        ],
        child: const MaterialApp(home: RestaurantPage()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Seat First Available Table'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Retry is available'), findsOneWidget);

    fakeRepo.shouldFailSeat = false;
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();

    expect(
      adapter.events,
      containsAll([
        'restaurant_ops_table_seat_failed',
        'restaurant_ops_table_seated',
      ]),
    );
  });
}
