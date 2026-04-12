export type TableStatus = 'available' | 'occupied' | 'reserved' | 'out_of_service';
export type WaitlistStatus = 'waiting' | 'seated' | 'cancelled';
export type OrderStatus = 'draft' | 'submitted' | 'in_progress' | 'ready' | 'served' | 'cancelled';
export type KitchenTicketStatus = 'queued' | 'in_preparation' | 'ready' | 'served' | 'delayed' | 'voided';

export interface RestaurantBranch {
  id: number;
  name: string;
  tax_rate: number;
  service_charge_rate: number;
  is_active: boolean;
}

export interface RestaurantTable {
  id: number;
  branch_id: number;
  code: string;
  seats: number;
  status: TableStatus;
}

export interface MenuItem {
  id: number;
  branch_id: number;
  name: string;
  price: number;
  is_available: boolean;
}

export interface Reservation {
  id: number;
  branch_id: number;
  guest_name: string;
  guest_phone: string;
  party_size: number;
  reservation_time: string;
  table_id: number | null;
  status: string;
  notes?: string | null;
}

export interface WaitlistEntry {
  id: number;
  branch_id: number;
  guest_name: string;
  guest_phone: string;
  party_size: number;
  status: WaitlistStatus;
  notes?: string | null;
}

export interface KitchenTicket {
  id: number;
  order_item_id: number;
  station: string;
  status: KitchenTicketStatus;
  priority: number;
  updated_at: string;
}

export interface CursorPage<T> {
  items: T[];
  next_cursor: number | null;
}

export interface RestaurantOrder {
  id: number;
  branch_id: number;
  table_id: number | null;
  waiter_id: number | null;
  order_source: string;
  status: OrderStatus;
  created_at: string;
  updated_at: string;
}

export interface Bill {
  id: number;
  order_id: number;
  subtotal: number;
  tax_amount: number;
  service_charge: number;
  total_amount: number;
  paid_amount: number;
  status: 'open' | 'partially_paid' | 'paid' | 'voided';
}

export interface OrderEditApproval {
  id: number;
  order_id: number;
  requested_by: number;
  approved_by: number | null;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface BranchOperationsReport {
  branch_id: number;
  orders_count: number;
  open_tickets: number;
  service_delay_count: number;
  gross_sales: number;
  collected_sales: number;
  low_stock_count: number;
  staffing: {
    scheduled_shift_count: number;
    checked_in_count: number;
    coverage_gap_count: number;
  };
  settlement_health: {
    open_drawers: number;
    unpaid_bills: number;
    failed_exports: number;
  };
  readiness: {
    has_active_drawer: boolean;
    has_scheduled_staff: boolean;
    critical_stock_risk: boolean;
    settlement_blocked: boolean;
  };
  operational_exception_count: number;
  generated_at: string;
}

export interface OperationalNotification {
  id: number;
  branch_id: number;
  event_name: string;
  severity: 'info' | 'warning' | 'critical';
  source: string;
  actor_user_id: number | null;
  payload_json: string | null;
  is_operational_exception: boolean;
  occurred_at: string;
}
