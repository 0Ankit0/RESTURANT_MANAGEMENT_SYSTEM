import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/analytics/analytics_events.dart';
import '../../../../core/analytics/analytics_provider.dart';
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

final restaurantKitchenTicketsProvider = FutureProvider<CursorPage<KitchenTicketItem>>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getKitchenTickets(branchId: branchId);
});

final restaurantStockAlertsProvider = FutureProvider<List<StockAlertItem>>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getStockAlerts(branchId);
});

final restaurantBillsProvider = FutureProvider<List<RestaurantBillItem>>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getBills(branchId);
});

final restaurantOperationalNotificationsProvider =
    FutureProvider<List<OperationalNotificationItem>>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getOperationalNotifications(branchId);
});

final restaurantBranchReportProvider = FutureProvider<BranchOperationsReport>((ref) {
  final branchId = ref.watch(selectedBranchIdProvider);
  return ref.watch(restaurantRepositoryProvider).getBranchReport(branchId);
});

enum RestaurantActionType {
  createReservation,
  seatTable,
  promoteWaitlist,
  updateKitchenTicket,
  settleBill,
}

class RestaurantActionState {
  final RestaurantActionType? type;
  final bool isLoading;
  final String? error;
  final String? successMessage;
  final int retryCount;
  final int? branchId;

  const RestaurantActionState({
    this.type,
    this.isLoading = false,
    this.error,
    this.successMessage,
    this.retryCount = 0,
    this.branchId,
  });

  bool get canRetry => !isLoading && error != null && type != null;

  RestaurantActionState copyWith({
    RestaurantActionType? type,
    bool? isLoading,
    String? error,
    bool clearError = false,
    String? successMessage,
    bool clearSuccess = false,
    int? retryCount,
    int? branchId,
  }) {
    return RestaurantActionState(
      type: type ?? this.type,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      successMessage: clearSuccess ? null : (successMessage ?? this.successMessage),
      retryCount: retryCount ?? this.retryCount,
      branchId: branchId ?? this.branchId,
    );
  }
}

final restaurantActionControllerProvider =
    StateNotifierProvider<RestaurantActionController, RestaurantActionState>((ref) {
  return RestaurantActionController(ref);
});

class RestaurantActionController extends StateNotifier<RestaurantActionState> {
  final Ref ref;
  Future<void> Function()? _lastRetry;

  RestaurantActionController(this.ref) : super(const RestaurantActionState());

  Future<void> createReservation({
    required int branchId,
    required String guestName,
    required String guestPhone,
    required int partySize,
  }) {
    return _execute(
      type: RestaurantActionType.createReservation,
      branchId: branchId,
      successMessage: 'Reservation created.',
      successEvent: RestaurantAnalyticsEvents.reservationCreated,
      failureEvent: RestaurantAnalyticsEvents.reservationCreateFailed,
      eventProperties: {'branch_id': branchId, 'party_size': partySize},
      action: () => ref.read(restaurantRepositoryProvider).createReservation(
            branchId: branchId,
            guestName: guestName,
            guestPhone: guestPhone,
            partySize: partySize,
          ),
      onSuccess: () {
        ref.invalidate(restaurantBranchReportProvider);
      },
      retryAction: () => createReservation(
        branchId: branchId,
        guestName: guestName,
        guestPhone: guestPhone,
        partySize: partySize,
      ),
    );
  }

  Future<void> seatFirstAvailableTable({required int branchId}) async {
    final tables = await ref.read(restaurantTablesProvider.future);
    final available = tables.where((table) => table.status == 'available').toList();
    if (available.isEmpty) {
      state = state.copyWith(
        type: RestaurantActionType.seatTable,
        branchId: branchId,
        error: 'No available table to seat right now.',
        clearSuccess: true,
      );
      return;
    }

    return _execute(
      type: RestaurantActionType.seatTable,
      branchId: branchId,
      successMessage: 'Table ${available.first.code} seated successfully.',
      successEvent: RestaurantAnalyticsEvents.tableSeated,
      failureEvent: RestaurantAnalyticsEvents.tableSeatFailed,
      eventProperties: {'branch_id': branchId, 'table_id': available.first.id},
      action: () => ref.read(restaurantRepositoryProvider).seatTable(
            tableId: available.first.id,
            partySize: 2,
          ),
      onSuccess: () {
        ref.invalidate(restaurantTablesProvider);
        ref.invalidate(restaurantOrdersProvider);
      },
      retryAction: () => seatFirstAvailableTable(branchId: branchId),
    );
  }

  Future<void> promoteFirstWaitlist({required int branchId}) async {
    final tables = await ref.read(restaurantTablesProvider.future);
    final waitlist = await ref.read(restaurantWaitlistProvider.future);

    final available = tables.where((table) => table.status == 'available').toList();
    final waiting = waitlist.items.where((entry) => entry.status == 'waiting').toList();
    if (available.isEmpty || waiting.isEmpty) {
      state = state.copyWith(
        type: RestaurantActionType.promoteWaitlist,
        branchId: branchId,
        error: 'Need one waiting guest and one available table for promotion.',
        clearSuccess: true,
      );
      return;
    }

    return _execute(
      type: RestaurantActionType.promoteWaitlist,
      branchId: branchId,
      successMessage: 'Promoted ${waiting.first.guestName} to table ${available.first.code}.',
      successEvent: RestaurantAnalyticsEvents.waitlistPromoted,
      failureEvent: RestaurantAnalyticsEvents.waitlistPromoteFailed,
      eventProperties: {
        'branch_id': branchId,
        'waitlist_id': waiting.first.id,
        'table_id': available.first.id,
      },
      action: () => ref.read(restaurantRepositoryProvider).promoteWaitlist(
            waitlistId: waiting.first.id,
            tableId: available.first.id,
          ),
      onSuccess: () {
        ref.invalidate(restaurantWaitlistProvider);
        ref.invalidate(restaurantTablesProvider);
      },
      retryAction: () => promoteFirstWaitlist(branchId: branchId),
    );
  }

  Future<void> advanceKitchenTicket({
    required int branchId,
    required int ticketId,
    required String nextStatus,
  }) {
    return _execute(
      type: RestaurantActionType.updateKitchenTicket,
      branchId: branchId,
      successMessage: 'Ticket #$ticketId moved to $nextStatus.',
      successEvent: RestaurantAnalyticsEvents.kitchenTicketUpdated,
      failureEvent: RestaurantAnalyticsEvents.kitchenTicketUpdateFailed,
      eventProperties: {
        'branch_id': branchId,
        'ticket_id': ticketId,
        'status': nextStatus,
      },
      action: () => ref.read(restaurantRepositoryProvider).updateKitchenTicket(
            ticketId: ticketId,
            status: nextStatus,
          ),
      onSuccess: () {
        ref.invalidate(restaurantKitchenTicketsProvider);
        ref.invalidate(restaurantBranchReportProvider);
      },
      retryAction: () => advanceKitchenTicket(
        branchId: branchId,
        ticketId: ticketId,
        nextStatus: nextStatus,
      ),
    );
  }

  Future<void> settleFirstOpenBill({required int branchId}) async {
    final bills = await ref.read(restaurantBillsProvider.future);
    final target = bills.where((bill) => bill.status != 'paid').toList();
    if (target.isEmpty) {
      state = state.copyWith(
        type: RestaurantActionType.settleBill,
        branchId: branchId,
        error: 'No unsettled bill available.',
        clearSuccess: true,
      );
      return;
    }

    final selected = target.first;
    final remaining = (selected.totalAmount - selected.paidAmount).clamp(0, double.infinity);
    if (remaining <= 0) {
      state = state.copyWith(
        type: RestaurantActionType.settleBill,
        branchId: branchId,
        error: 'Selected bill has no remaining balance.',
        clearSuccess: true,
      );
      return;
    }

    return _execute(
      type: RestaurantActionType.settleBill,
      branchId: branchId,
      successMessage: 'Bill #${selected.id} settled.',
      successEvent: RestaurantAnalyticsEvents.billSettled,
      failureEvent: RestaurantAnalyticsEvents.billSettleFailed,
      eventProperties: {'branch_id': branchId, 'bill_id': selected.id, 'amount': remaining},
      action: () => ref.read(restaurantRepositoryProvider).settleBill(
            billId: selected.id,
            amount: remaining,
            paymentMethod: 'cash',
          ),
      onSuccess: () {
        ref.invalidate(restaurantBillsProvider);
        ref.invalidate(restaurantBranchReportProvider);
      },
      retryAction: () => settleFirstOpenBill(branchId: branchId),
    );
  }

  Future<void> retryLastAction() async {
    final retry = _lastRetry;
    if (retry == null || !state.canRetry) return;
    state = state.copyWith(
      isLoading: true,
      clearError: true,
      clearSuccess: true,
      retryCount: state.retryCount + 1,
    );
    await retry();
  }

  void clearMessages() {
    state = state.copyWith(clearError: true, clearSuccess: true);
  }

  Future<void> _execute({
    required RestaurantActionType type,
    required int branchId,
    required Future<void> Function() action,
    required Future<void> Function() retryAction,
    required String successEvent,
    required String failureEvent,
    required String successMessage,
    required Map<String, Object> eventProperties,
    void Function()? onSuccess,
  }) async {
    state = state.copyWith(
      type: type,
      branchId: branchId,
      isLoading: true,
      clearError: true,
      clearSuccess: true,
    );

    try {
      await action();
      onSuccess?.call();
      await ref.read(analyticsServiceProvider).capture(successEvent, eventProperties);
      state = state.copyWith(
        isLoading: false,
        successMessage: successMessage,
        clearError: true,
      );
      _lastRetry = null;
    } catch (error) {
      _lastRetry = retryAction;
      await ref.read(analyticsServiceProvider).capture(
        failureEvent,
        {
          ...eventProperties,
          'error': error.toString(),
          'retry_count': state.retryCount,
        },
      );
      state = state.copyWith(
        isLoading: false,
        error: error.toString(),
        clearSuccess: true,
      );
    }
  }
}
