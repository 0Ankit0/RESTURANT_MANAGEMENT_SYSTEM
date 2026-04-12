import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/restaurant/data/models/restaurant_models.dart';
import 'package:mobile/features/restaurant/presentation/pages/restaurant_page.dart';
import 'package:mobile/features/restaurant/presentation/providers/restaurant_provider.dart';

class FakeRestaurantActionController extends StateNotifier<RestaurantActionState> {
  FakeRestaurantActionController() : super(const RestaurantActionState());

  int seatCalls = 0;
  int promoteCalls = 0;
  int settleCalls = 0;

  Future<void> seatFirstAvailableTable({required int branchId}) async {
    seatCalls += 1;
    state = state.copyWith(successMessage: 'seat-ok', clearError: true);
  }

  Future<void> promoteFirstWaitlist({required int branchId}) async {
    promoteCalls += 1;
    state = state.copyWith(successMessage: 'promote-ok', clearError: true);
  }

  Future<void> settleFirstOpenBill({required int branchId}) async {
    settleCalls += 1;
    state = state.copyWith(successMessage: 'settle-ok', clearError: true);
  }

  Future<void> createReservation({required int branchId, required String guestName, required String guestPhone, required int partySize}) async {}
  Future<void> advanceKitchenTicket({required int branchId, required int ticketId, required String nextStatus}) async {}
  Future<void> retryLastAction() async {}
}

void main() {
  testWidgets('branch operation buttons trigger action controller transitions', (tester) async {
    final fakeController = FakeRestaurantActionController();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          selectedBranchIdProvider.overrideWith((ref) => 2),
          restaurantBranchesProvider.overrideWith((ref) async => [RestaurantBranchItem(id: 2, name: 'Downtown')]),
          restaurantTablesProvider.overrideWith((ref) async => [RestaurantTableItem(id: 10, code: 'T10', status: 'available', seats: 4)]),
          restaurantBranchReportProvider.overrideWith((ref) async => BranchOperationsReport(branchId: 2, ordersCount: 1, openTickets: 1, grossSales: 100, collectedSales: 80, lowStockCount: 0, settlementHealth: SettlementHealth.empty())),
          restaurantOrdersProvider.overrideWith((ref) async => CursorPage(items: [RestaurantOrderItem(id: 99, status: 'submitted')], nextCursor: null)),
          restaurantWaitlistProvider.overrideWith((ref) async => CursorPage(items: [RestaurantWaitlistItem(id: 7, guestName: 'Walkin', partySize: 2, status: 'waiting')], nextCursor: null)),
          restaurantKitchenTicketsProvider.overrideWith((ref) async => CursorPage(items: [KitchenTicketItem(id: 1, station: 'line', status: 'queued', priority: 1, updatedAt: null)], nextCursor: null)),
          restaurantOperationalNotificationsProvider.overrideWith((ref) async => []),
          restaurantStockAlertsProvider.overrideWith((ref) async => []),
          restaurantActionControllerProvider.overrideWith((ref) => fakeController),
        ],
        child: const MaterialApp(home: RestaurantPage()),
      ),
    );

    await tester.pumpAndSettle();

    await tester.tap(find.text('Seat First Available Table'));
    await tester.pump();
    await tester.tap(find.text('Promote First Waitlist'));
    await tester.pump();
    await tester.tap(find.text('Settle First Open Bill'));
    await tester.pump();

    expect(fakeController.seatCalls, 1);
    expect(fakeController.promoteCalls, 1);
    expect(fakeController.settleCalls, 1);
  });
}
