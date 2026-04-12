import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/restaurant_provider.dart';

class RestaurantPage extends ConsumerStatefulWidget {
  const RestaurantPage({super.key});

  @override
  ConsumerState<RestaurantPage> createState() => _RestaurantPageState();
}

class _RestaurantPageState extends ConsumerState<RestaurantPage> {
  final _guestNameController = TextEditingController(text: 'Walk-in Guest');
  final _guestPhoneController = TextEditingController(text: '+10000000000');
  final _partySizeController = TextEditingController(text: '2');

  @override
  void initState() {
    super.initState();
    ref.listenManual<RestaurantActionState>(
      restaurantActionControllerProvider,
      (previous, next) {
        if (!mounted) return;
        if (next.error != null && next.error != previous?.error) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(next.error!), backgroundColor: Colors.red),
          );
        } else if (next.successMessage != null && next.successMessage != previous?.successMessage) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(next.successMessage!)),
          );
        }
      },
    );
  }

  @override
  void dispose() {
    _guestNameController.dispose();
    _guestPhoneController.dispose();
    _partySizeController.dispose();
    super.dispose();
  }

  Future<void> _createReservation() async {
    final branchId = ref.read(selectedBranchIdProvider);
    final partySize = int.tryParse(_partySizeController.text) ?? 1;
    await ref.read(restaurantActionControllerProvider.notifier).createReservation(
          branchId: branchId,
          guestName: _guestNameController.text,
          guestPhone: _guestPhoneController.text,
          partySize: partySize,
        );
  }

  Future<void> _seatFirstAvailableTable() {
    final branchId = ref.read(selectedBranchIdProvider);
    return ref.read(restaurantActionControllerProvider.notifier).seatFirstAvailableTable(
          branchId: branchId,
        );
  }

  Future<void> _promoteFirstWaitlist() {
    final branchId = ref.read(selectedBranchIdProvider);
    return ref.read(restaurantActionControllerProvider.notifier).promoteFirstWaitlist(
          branchId: branchId,
        );
  }

  Future<void> _settleFirstOpenBill() {
    final branchId = ref.read(selectedBranchIdProvider);
    return ref.read(restaurantActionControllerProvider.notifier).settleFirstOpenBill(
          branchId: branchId,
        );
  }

  Future<void> _advanceKitchenTicket(int ticketId, String currentStatus) {
    final branchId = ref.read(selectedBranchIdProvider);
    final next = _nextKitchenStatus(currentStatus);
    if (next == null) return Future.value();
    return ref.read(restaurantActionControllerProvider.notifier).advanceKitchenTicket(
          branchId: branchId,
          ticketId: ticketId,
          nextStatus: next,
        );
  }

  Future<void> _transitionReservation(int reservationId, String nextStatus) {
    final branchId = ref.read(selectedBranchIdProvider);
    return ref.read(restaurantActionControllerProvider.notifier).transitionReservation(
          branchId: branchId,
          reservationId: reservationId,
          nextStatus: nextStatus,
        );
  }

  Future<void> _advanceOrder(int orderId, String currentStatus) {
    final next = _nextOrderStatus(currentStatus);
    if (next == null) return Future.value();
    final branchId = ref.read(selectedBranchIdProvider);
    return ref.read(restaurantActionControllerProvider.notifier).advanceOrder(
          branchId: branchId,
          orderId: orderId,
          nextStatus: next,
        );
  }

  String? _nextKitchenStatus(String status) {
    switch (status) {
      case 'queued':
        return 'in_preparation';
      case 'in_preparation':
        return 'ready';
      case 'ready':
        return 'served';
      default:
        return null;
    }
  }

  String? _nextOrderStatus(String status) {
    switch (status) {
      case 'submitted':
        return 'in_progress';
      case 'in_progress':
        return 'ready';
      case 'ready':
        return 'served';
      default:
        return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final branchId = ref.watch(selectedBranchIdProvider);
    final actionState = ref.watch(restaurantActionControllerProvider);
    final branchesAsync = ref.watch(restaurantBranchesProvider);
    final tablesAsync = ref.watch(restaurantTablesProvider);
    final reportAsync = ref.watch(restaurantBranchReportProvider);
    final ordersAsync = ref.watch(restaurantOrdersProvider);
    final waitlistAsync = ref.watch(restaurantWaitlistProvider);
    final reservationsAsync = ref.watch(restaurantReservationsProvider);
    final kitchenAsync = ref.watch(restaurantKitchenTicketsProvider);
    final notificationsAsync = ref.watch(restaurantOperationalNotificationsProvider);
    final stockAlertsAsync = ref.watch(restaurantStockAlertsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Restaurant Operations')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              const Text('Branch: '),
              const SizedBox(width: 8),
              branchesAsync.when(
                data: (branches) => DropdownButton<int>(
                  value: branches.any((b) => b.id == branchId)
                      ? branchId
                      : (branches.isNotEmpty ? branches.first.id : null),
                  items: branches
                      .map(
                        (branch) => DropdownMenuItem<int>(
                          value: branch.id,
                          child: Text('${branch.name} (#${branch.id})'),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value != null) {
                      ref.read(selectedBranchIdProvider.notifier).state = value;
                    }
                  },
                ),
                loading: () => const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                error: (_, __) => const Text('Failed to load branches'),
              ),
              const Spacer(),
              IconButton(
                tooltip: 'Refresh branch data',
                onPressed: () {
                  ref.invalidate(restaurantBranchReportProvider);
                  ref.invalidate(restaurantTablesProvider);
                  ref.invalidate(restaurantOrdersProvider);
                  ref.invalidate(restaurantWaitlistProvider);
                  ref.invalidate(restaurantKitchenTicketsProvider);
                  ref.invalidate(restaurantStockAlertsProvider);
                  ref.invalidate(restaurantOperationalNotificationsProvider);
                },
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          if (actionState.canRetry) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Last action failed. Retry is available for branch #${actionState.branchId}.',
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
                TextButton(
                  onPressed: actionState.isLoading
                      ? null
                      : () => ref.read(restaurantActionControllerProvider.notifier).retryLastAction(),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ],
          const SizedBox(height: 16),
          reportAsync.when(
            data: (report) => Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _MetricCard(label: 'Orders', value: '${report.ordersCount}'),
                _MetricCard(label: 'Open Tickets', value: '${report.openTickets}'),
                _MetricCard(label: 'Gross', value: report.grossSales.toStringAsFixed(2)),
                _MetricCard(label: 'Low Stock', value: '${report.lowStockCount}'),
              ],
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load report: $error'),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Create Reservation', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  TextField(controller: _guestNameController, decoration: const InputDecoration(labelText: 'Guest name')),
                  TextField(controller: _guestPhoneController, decoration: const InputDecoration(labelText: 'Guest phone')),
                  TextField(controller: _partySizeController, decoration: const InputDecoration(labelText: 'Party size')),
                  const SizedBox(height: 8),
                  FilledButton(
                    onPressed: actionState.isLoading ? null : _createReservation,
                    child: const Text('Create Reservation'),
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton(
                    onPressed: actionState.isLoading ? null : _seatFirstAvailableTable,
                    child: const Text('Seat First Available Table'),
                  ),
                  OutlinedButton(
                    onPressed: actionState.isLoading ? null : _promoteFirstWaitlist,
                    child: const Text('Promote First Waitlist'),
                  ),
                  OutlinedButton(
                    onPressed: actionState.isLoading ? null : _settleFirstOpenBill,
                    child: const Text('Settle First Open Bill'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text('Tables', style: TextStyle(fontWeight: FontWeight.bold)),
          tablesAsync.when(
            data: (tables) => Column(
              children: tables
                  .map(
                    (table) => Card(
                      child: ListTile(
                        title: Text(table.code),
                        subtitle: Text('Seats ${table.seats}'),
                        trailing: Text(table.status),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load tables: $error'),
          ),
          const SizedBox(height: 16),
          const Text('Waitlist', style: TextStyle(fontWeight: FontWeight.bold)),
          waitlistAsync.when(
            data: (waitlistPage) => Column(
              children: waitlistPage.items
                  .map(
                    (entry) => Card(
                      child: ListTile(
                        title: Text(entry.guestName),
                        subtitle: Text('Party ${entry.partySize}'),
                        trailing: Text(entry.status),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load waitlist: $error'),
          ),
          const SizedBox(height: 16),
          const Text('Reservations', style: TextStyle(fontWeight: FontWeight.bold)),
          reservationsAsync.when(
            data: (reservations) => Column(
              children: reservations
                  .map(
                    (reservation) => Card(
                      child: ListTile(
                        title: Text(reservation.guestName),
                        subtitle: Text('Party ${reservation.partySize} · ${reservation.status}'),
                        trailing: Wrap(
                          spacing: 8,
                          children: [
                            if (reservation.status == 'pending')
                              TextButton(
                                onPressed: actionState.isLoading
                                    ? null
                                    : () => _transitionReservation(reservation.id, 'confirmed'),
                                child: const Text('Confirm'),
                              ),
                            if (reservation.status != 'cancelled' && reservation.status != 'seated')
                              TextButton(
                                onPressed: actionState.isLoading
                                    ? null
                                    : () => _transitionReservation(reservation.id, 'cancelled'),
                                child: const Text('Cancel'),
                              ),
                          ],
                        ),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load reservations: $error'),
          ),
          const SizedBox(height: 16),
          const Text('Kitchen Queue', style: TextStyle(fontWeight: FontWeight.bold)),
          kitchenAsync.when(
            data: (kitchenPage) => Column(
              children: kitchenPage.items
                  .map(
                    (ticket) => Card(
                      child: ListTile(
                        title: Text('Ticket #${ticket.id} (${ticket.station})'),
                        subtitle: Text('Priority ${ticket.priority}'),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(ticket.status),
                            const SizedBox(width: 8),
                            if (_nextKitchenStatus(ticket.status) != null)
                              TextButton(
                                onPressed: actionState.isLoading
                                    ? null
                                    : () => _advanceKitchenTicket(ticket.id, ticket.status),
                                child: const Text('Advance'),
                              ),
                          ],
                        ),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load kitchen tickets: $error'),
          ),
          const SizedBox(height: 16),
          const Text('Settlement Health', style: TextStyle(fontWeight: FontWeight.bold)),
          reportAsync.when(
            data: (report) => Card(
              child: ListTile(
                title: Text(
                  'Open drawers ${report.settlementHealth.openDrawers} · '
                  'Unpaid bills ${report.settlementHealth.unpaidBills} · '
                  'Failed exports ${report.settlementHealth.failedExports}',
                ),
              ),
            ),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 16),
          const Text('Low Stock Alerts', style: TextStyle(fontWeight: FontWeight.bold)),
          stockAlertsAsync.when(
            data: (alerts) => Column(
              children: alerts
                  .map(
                    (alert) => Card(
                      child: ListTile(
                        title: Text(alert.itemName),
                        subtitle: Text('Units left: ${alert.availableUnits}'),
                        trailing: Text(alert.severity),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load stock alerts: $error'),
          ),
          const SizedBox(height: 16),
          const Text('Operational Notifications', style: TextStyle(fontWeight: FontWeight.bold)),
          notificationsAsync.when(
            data: (notifications) => Column(
              children: notifications
                  .map(
                    (notice) => Card(
                      child: ListTile(
                        title: Text(notice.eventName),
                        subtitle: Text(notice.occurredAt?.toLocal().toString() ?? '-'),
                        trailing: Text(notice.severity),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load notifications: $error'),
          ),
          const SizedBox(height: 16),
          const Text('Recent Orders', style: TextStyle(fontWeight: FontWeight.bold)),
          ordersAsync.when(
            data: (ordersPage) => Column(
              children: ordersPage.items
                  .map(
                    (order) => Card(
                      child: ListTile(
                        title: Text('Order #${order.id}'),
                        subtitle: Text(order.status),
                        trailing: _nextOrderStatus(order.status) == null
                            ? null
                            : TextButton(
                                onPressed: actionState.isLoading
                                    ? null
                                    : () => _advanceOrder(order.id, order.status),
                                child: Text('To ${_nextOrderStatus(order.status)}'),
                              ),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Text('Failed to load orders: $error'),
          ),
        ],
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;

  const _MetricCard({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
