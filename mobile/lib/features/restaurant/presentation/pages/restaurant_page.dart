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
  void dispose() {
    _guestNameController.dispose();
    _guestPhoneController.dispose();
    _partySizeController.dispose();
    super.dispose();
  }

  Future<void> _createReservation() async {
    final branchId = ref.read(selectedBranchIdProvider);
    final partySize = int.tryParse(_partySizeController.text) ?? 1;

    await ref.read(restaurantRepositoryProvider).createReservation(
      branchId: branchId,
      guestName: _guestNameController.text,
      guestPhone: _guestPhoneController.text,
      partySize: partySize,
    );

    ref.invalidate(restaurantBranchReportProvider);

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Reservation created')),
    );
  }

  Future<void> _seatFirstAvailableTable() async {
    final tables = await ref.read(restaurantTablesProvider.future);
    final available = tables.where((table) => table.status == 'available').toList();
    if (available.isEmpty) return;

    await ref.read(restaurantRepositoryProvider).seatTable(tableId: available.first.id, partySize: 2);
    ref.invalidate(restaurantTablesProvider);
    ref.invalidate(restaurantOrdersProvider);
  }

  Future<void> _promoteFirstWaitlist() async {
    final tables = await ref.read(restaurantTablesProvider.future);
    final waitlist = await ref.read(restaurantWaitlistProvider.future);

    final available = tables.where((table) => table.status == 'available').toList();
    final waiting = waitlist.items.where((entry) => entry.status == 'waiting').toList();
    if (available.isEmpty || waiting.isEmpty) return;

    await ref.read(restaurantRepositoryProvider).promoteWaitlist(
      waitlistId: waiting.first.id,
      tableId: available.first.id,
    );

    ref.invalidate(restaurantWaitlistProvider);
    ref.invalidate(restaurantTablesProvider);
  }

  @override
  Widget build(BuildContext context) {
    final branchId = ref.watch(selectedBranchIdProvider);
    final branchesAsync = ref.watch(restaurantBranchesProvider);
    final tablesAsync = ref.watch(restaurantTablesProvider);
    final reportAsync = ref.watch(restaurantBranchReportProvider);
    final ordersAsync = ref.watch(restaurantOrdersProvider);
    final waitlistAsync = ref.watch(restaurantWaitlistProvider);

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
            ],
          ),
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
                  FilledButton(onPressed: _createReservation, child: const Text('Create Reservation')),
                  const SizedBox(height: 8),
                  OutlinedButton(onPressed: _seatFirstAvailableTable, child: const Text('Seat First Available Table')),
                  OutlinedButton(onPressed: _promoteFirstWaitlist, child: const Text('Promote First Waitlist')),
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
          const Text('Recent Orders', style: TextStyle(fontWeight: FontWeight.bold)),
          ordersAsync.when(
            data: (ordersPage) => Column(
              children: ordersPage.items
                  .map(
                    (order) => Card(
                      child: ListTile(
                        title: Text('Order #${order.id}'),
                        trailing: Text(order.status),
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
