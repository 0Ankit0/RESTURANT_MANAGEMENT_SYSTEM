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

class RestaurantReservationItem {
  final int id;
  final String guestName;
  final int partySize;
  final String status;

  RestaurantReservationItem({
    required this.id,
    required this.guestName,
    required this.partySize,
    required this.status,
  });

  factory RestaurantReservationItem.fromJson(Map<String, dynamic> json) {
    return RestaurantReservationItem(
      id: json['id'] as int,
      guestName: json['guest_name'] as String? ?? 'Guest',
      partySize: json['party_size'] as int? ?? 1,
      status: json['status'] as String? ?? 'pending',
    );
  }
}

class KitchenTicketItem {
  final int id;
  final String station;
  final String status;
  final int priority;
  final DateTime? updatedAt;

  KitchenTicketItem({
    required this.id,
    required this.station,
    required this.status,
    required this.priority,
    required this.updatedAt,
  });

  factory KitchenTicketItem.fromJson(Map<String, dynamic> json) {
    return KitchenTicketItem(
      id: json['id'] as int,
      station: json['station'] as String? ?? 'line',
      status: json['status'] as String? ?? 'queued',
      priority: json['priority'] as int? ?? 0,
      updatedAt: DateTime.tryParse(json['updated_at'] as String? ?? ''),
    );
  }
}

class StockAlertItem {
  final int id;
  final int? branchId;
  final String itemName;
  final String severity;
  final int availableUnits;

  StockAlertItem({
    required this.id,
    required this.branchId,
    required this.itemName,
    required this.severity,
    required this.availableUnits,
  });

  factory StockAlertItem.fromJson(Map<String, dynamic> json) {
    return StockAlertItem(
      id: json['id'] as int,
      branchId: json['branch_id'] as int?,
      itemName: json['item_name'] as String? ?? 'Inventory Item',
      severity: json['severity'] as String? ?? 'warning',
      availableUnits: json['available_units'] as int? ?? 0,
    );
  }
}

class SettlementHealth {
  final int openDrawers;
  final int unpaidBills;
  final int failedExports;

  SettlementHealth({
    required this.openDrawers,
    required this.unpaidBills,
    required this.failedExports,
  });

  factory SettlementHealth.fromJson(Map<String, dynamic> json) {
    return SettlementHealth(
      openDrawers: json['open_drawers'] as int? ?? 0,
      unpaidBills: json['unpaid_bills'] as int? ?? 0,
      failedExports: json['failed_exports'] as int? ?? 0,
    );
  }

  static SettlementHealth empty() =>
      SettlementHealth(openDrawers: 0, unpaidBills: 0, failedExports: 0);
}

class RestaurantBillItem {
  final int id;
  final double totalAmount;
  final double paidAmount;
  final String status;

  RestaurantBillItem({
    required this.id,
    required this.totalAmount,
    required this.paidAmount,
    required this.status,
  });

  factory RestaurantBillItem.fromJson(Map<String, dynamic> json) {
    return RestaurantBillItem(
      id: json['id'] as int,
      totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0,
      paidAmount: (json['paid_amount'] as num?)?.toDouble() ?? 0,
      status: json['status'] as String? ?? 'open',
    );
  }
}

class OperationalNotificationItem {
  final int id;
  final int branchId;
  final String eventName;
  final String severity;
  final DateTime? occurredAt;

  OperationalNotificationItem({
    required this.id,
    required this.branchId,
    required this.eventName,
    required this.severity,
    required this.occurredAt,
  });

  factory OperationalNotificationItem.fromJson(Map<String, dynamic> json) {
    return OperationalNotificationItem(
      id: json['id'] as int,
      branchId: json['branch_id'] as int? ?? 0,
      eventName: json['event_name'] as String? ?? 'Operational event',
      severity: json['severity'] as String? ?? 'info',
      occurredAt: DateTime.tryParse(json['occurred_at'] as String? ?? ''),
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
  final SettlementHealth settlementHealth;

  BranchOperationsReport({
    required this.branchId,
    required this.ordersCount,
    required this.openTickets,
    required this.grossSales,
    required this.collectedSales,
    required this.lowStockCount,
    required this.settlementHealth,
  });

  factory BranchOperationsReport.fromJson(Map<String, dynamic> json) {
    return BranchOperationsReport(
      branchId: json['branch_id'] as int? ?? 0,
      ordersCount: json['orders_count'] as int? ?? 0,
      openTickets: json['open_tickets'] as int? ?? 0,
      grossSales: (json['gross_sales'] as num?)?.toDouble() ?? 0,
      collectedSales: (json['collected_sales'] as num?)?.toDouble() ?? 0,
      lowStockCount: json['low_stock_count'] as int? ?? 0,
      settlementHealth: SettlementHealth.fromJson(
        json['settlement_health'] as Map<String, dynamic>? ?? const {},
      ),
    );
  }
}

class DayCloseItem {
  final int id;
  final int branchId;
  final String status;

  DayCloseItem({
    required this.id,
    required this.branchId,
    required this.status,
  });

  factory DayCloseItem.fromJson(Map<String, dynamic> json) {
    return DayCloseItem(
      id: json['id'] as int,
      branchId: json['branch_id'] as int? ?? 0,
      status: json['status'] as String? ?? 'open',
    );
  }
}

class DayCloseBlockerItem {
  final String blockerCode;
  final String severity;
  final int count;
  final String summary;

  DayCloseBlockerItem({
    required this.blockerCode,
    required this.severity,
    required this.count,
    required this.summary,
  });

  factory DayCloseBlockerItem.fromJson(Map<String, dynamic> json) {
    return DayCloseBlockerItem(
      blockerCode: json['blocker_code'] as String? ?? 'unknown',
      severity: json['severity'] as String? ?? 'warning',
      count: json['count'] as int? ?? 0,
      summary: json['summary'] as String? ?? 'Blocker detected',
    );
  }
}
