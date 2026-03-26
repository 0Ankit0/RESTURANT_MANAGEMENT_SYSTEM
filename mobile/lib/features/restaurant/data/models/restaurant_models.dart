class RestaurantBranchItem {
  final int id;
  final String name;

  RestaurantBranchItem({required this.id, required this.name});

  factory RestaurantBranchItem.fromJson(Map<String, dynamic> json) {
    return RestaurantBranchItem(
      id: json['id'] as int,
      name: json['name'] as String? ?? 'Branch',
    );
  }
}

class RestaurantTableItem {
  final int id;
  final String code;
  final String status;
  final int seats;

  RestaurantTableItem({
    required this.id,
    required this.code,
    required this.status,
    required this.seats,
  });

  factory RestaurantTableItem.fromJson(Map<String, dynamic> json) {
    return RestaurantTableItem(
      id: json['id'] as int,
      code: json['code'] as String? ?? '',
      status: json['status'] as String? ?? 'available',
      seats: json['seats'] as int? ?? 0,
    );
  }
}

class RestaurantOrderItem {
  final int id;
  final String status;

  RestaurantOrderItem({required this.id, required this.status});

  factory RestaurantOrderItem.fromJson(Map<String, dynamic> json) {
    return RestaurantOrderItem(
      id: json['id'] as int,
      status: json['status'] as String? ?? 'submitted',
    );
  }
}

class RestaurantWaitlistItem {
  final int id;
  final String guestName;
  final int partySize;
  final String status;

  RestaurantWaitlistItem({
    required this.id,
    required this.guestName,
    required this.partySize,
    required this.status,
  });

  factory RestaurantWaitlistItem.fromJson(Map<String, dynamic> json) {
    return RestaurantWaitlistItem(
      id: json['id'] as int,
      guestName: json['guest_name'] as String? ?? 'Guest',
      partySize: json['party_size'] as int? ?? 1,
      status: json['status'] as String? ?? 'waiting',
    );
  }
}

class CursorPage<T> {
  final List<T> items;
  final int? nextCursor;

  CursorPage({required this.items, required this.nextCursor});
}

class BranchOperationsReport {
  final int branchId;
  final int ordersCount;
  final int openTickets;
  final double grossSales;
  final double collectedSales;
  final int lowStockCount;

  BranchOperationsReport({
    required this.branchId,
    required this.ordersCount,
    required this.openTickets,
    required this.grossSales,
    required this.collectedSales,
    required this.lowStockCount,
  });

  factory BranchOperationsReport.fromJson(Map<String, dynamic> json) {
    return BranchOperationsReport(
      branchId: json['branch_id'] as int? ?? 0,
      ordersCount: json['orders_count'] as int? ?? 0,
      openTickets: json['open_tickets'] as int? ?? 0,
      grossSales: (json['gross_sales'] as num?)?.toDouble() ?? 0,
      collectedSales: (json['collected_sales'] as num?)?.toDouble() ?? 0,
      lowStockCount: json['low_stock_count'] as int? ?? 0,
    );
  }
}
