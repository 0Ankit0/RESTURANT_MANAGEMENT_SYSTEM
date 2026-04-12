'use client';

import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  useBranchBills,
  useBranchMenuItems,
  useBranchOperationsReport,
  useBranchOrders,
  useBranchReservations,
  useBranchTables,
  useBranchWaitlist,
  useCreateOrder,
  useCreateOrderEditApproval,
  useCreateReservation,
  useKitchenTickets,
  useOperationalNotifications,
  usePromoteWaitlist,
  useResolveOrderEditApproval,
  useRestaurantBranches,
  useSeatTable,
  useSettleBill,
  useUpdateKitchenTicket,
  useUpdateOrder,
} from '@/hooks/use-restaurant';
import { useAnalytics } from '@/hooks/use-analytics';
import { RestaurantOpsEvents } from '@/lib/analytics/events';
import { useAuthStore } from '@/store/auth-store';
import type { KitchenTicketStatus } from '@/types/restaurant';

export type StaffContext = {
  staffId: number | null;
  branchPreferences: number[];
};

const asPositiveNumber = (value: unknown): number | null => {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
};

const normalizeBranchPreferences = (value: unknown): number[] => {
  if (!Array.isArray(value)) return [];
  const normalized = value
    .map((entry) => {
      if (typeof entry === 'number' || typeof entry === 'string') {
        return asPositiveNumber(entry);
      }
      if (entry && typeof entry === 'object') {
        const record = entry as Record<string, unknown>;
        return asPositiveNumber(record.branch_id ?? record.branchId ?? record.id);
      }
      return null;
    })
    .filter((entry): entry is number => entry !== null);

  return Array.from(new Set(normalized));
};

const flattenMembershipBranchIds = (value: unknown): number[] => {
  if (!Array.isArray(value)) return [];
  return value.flatMap((entry) => {
    if (!entry || typeof entry !== 'object') return [];
    const record = entry as Record<string, unknown>;
    return normalizeBranchPreferences([
      record.branch_id,
      record.branchId,
      record.home_branch_id,
      record.homeBranchId,
      record.branch,
      record.branches,
      record.membership,
    ]);
  });
};

export const deriveStaffContext = (user: unknown): StaffContext => {
  if (!user || typeof user !== 'object') {
    return { staffId: null, branchPreferences: [] };
  }

  const record = user as Record<string, unknown>;
  const defaultBranch = asPositiveNumber(
    record.default_branch_id ?? record.defaultBranchId ?? record.branch_id ?? record.branchId
  );
  const membershipBranches = normalizeBranchPreferences(record.branch_memberships ?? record.branchMemberships ?? record.branches);
  const nestedMembershipBranches = flattenMembershipBranchIds(record.memberships ?? record.staff_memberships ?? record.staffMemberships);
  const fallbackBranches = normalizeBranchPreferences(record.assigned_branch_ids ?? record.assignedBranchIds);

  return {
    staffId: asPositiveNumber(record.staff_id ?? record.staffId ?? record.employee_id ?? record.employeeId ?? record.id),
    branchPreferences: Array.from(
      new Set([defaultBranch, ...membershipBranches, ...nestedMembershipBranches, ...fallbackBranches].filter((entry): entry is number => entry !== null))
    ),
  };
};

const ticketTransitions: Record<KitchenTicketStatus, KitchenTicketStatus | null> = {
  queued: 'in_preparation',
  in_preparation: 'ready',
  ready: 'served',
  served: null,
  delayed: 'in_preparation',
  voided: null,
};

export const nextTicketStatus = (status: KitchenTicketStatus): KitchenTicketStatus | null => ticketTransitions[status] ?? null;

const getErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error === 'object' && error !== null) {
    const maybeResponse = error as { response?: { data?: { detail?: string } } };
    if (maybeResponse.response?.data?.detail) {
      return maybeResponse.response.data.detail;
    }
  }
  return fallback;
};

export default function RestaurantOpsPage() {
  const user = useAuthStore((state) => state.user);
  const [branchId, setBranchId] = useState(0);
  const [guestName, setGuestName] = useState('');
  const [guestPhone, setGuestPhone] = useState('');
  const [partySize, setPartySize] = useState('');
  const [menuItemId, setMenuItemId] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [quickOrderError, setQuickOrderError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [approvalByOrder, setApprovalByOrder] = useState<Record<number, number>>({});

  const staffContext = useMemo(() => deriveStaffContext(user), [user]);

  const branches = useRestaurantBranches();
  const branchChoices = useMemo(() => {
    const allBranches = branches.data ?? [];
    if (!staffContext.branchPreferences.length) return allBranches;
    const allowed = new Set(staffContext.branchPreferences);
    return allBranches.filter((branch) => allowed.has(branch.id));
  }, [branches.data, staffContext.branchPreferences]);

  const availableBranchIds = useMemo(() => new Set(branchChoices.map((branch) => branch.id)), [branchChoices]);
  const resolvedBranchId = useMemo(() => {
    const preferred = staffContext.branchPreferences.find((candidate) => availableBranchIds.has(candidate));
    return preferred ?? (branchChoices[0]?.id ?? 0);
  }, [availableBranchIds, branchChoices, staffContext.branchPreferences]);

  useEffect(() => {
    if (branchId > 0 && availableBranchIds.has(branchId)) return;
    if (!resolvedBranchId) return;
    setBranchId(resolvedBranchId);
  }, [availableBranchIds, branchId, resolvedBranchId]);

  const tables = useBranchTables(branchId);
  const orders = useBranchOrders(branchId);
  const bills = useBranchBills(branchId);
  const waitlist = useBranchWaitlist(branchId);
  const menuItems = useBranchMenuItems(branchId);
  const reservations = useBranchReservations(branchId);
  const kitchen = useKitchenTickets();
  const notifications = useOperationalNotifications(branchId);
  const report = useBranchOperationsReport(branchId);
  const analytics = useAnalytics();
  const createReservation = useCreateReservation();
  const seatTable = useSeatTable();
  const promoteWaitlist = usePromoteWaitlist();
  const createOrder = useCreateOrder();
  const updateTicket = useUpdateKitchenTicket();
  const createEditApproval = useCreateOrderEditApproval();
  const resolveApproval = useResolveOrderEditApproval();
  const updateOrder = useUpdateOrder();
  const settleBill = useSettleBill();

  useEffect(() => {
    if (branchId > 0) {
      analytics.capture(RestaurantOpsEvents.DASHBOARD_VIEWED, { branch_id: branchId });
    }
  }, [analytics, branchId]);

  const hasBranchAssignment = branchId > 0;
  const hasEligibleStaffContext = staffContext.staffId !== null;
  const branchGuardMessage = !hasBranchAssignment
    ? 'No branch is assigned to your account yet. Please contact an administrator before using Restaurant Operations.'
    : null;
  const staffGuardMessage = !hasEligibleStaffContext
    ? 'No eligible staff profile is linked to your user. Staff actions are disabled until staff context is available.'
    : null;

  const seatFirstTable = async () => {
    const table = tables.data?.find((row) => row.status === 'available');
    if (!table) {
      setActionError('No available table to seat right now.');
      return;
    }

    setActionError(null);
    setActionSuccess(null);
    try {
      await seatTable.mutateAsync({ branchId, tableId: table.id, partySize: 2 });
      setActionSuccess(`Table ${table.code} seated successfully.`);
    } catch (error) {
      setActionError(getErrorMessage(error, 'Unable to seat table.'));
    }
  };

  const promoteFirstWaitlist = async () => {
    const entry = waitlist.data?.items?.find((row) => row.status === 'waiting');
    const table = tables.data?.find((row) => row.status === 'available');
    if (!entry || !table) {
      setActionError('Need one waiting guest and one available table for promotion.');
      return;
    }

    setActionError(null);
    setActionSuccess(null);
    try {
      await promoteWaitlist.mutateAsync({ branchId, waitlistId: entry.id, tableId: table.id });
      setActionSuccess(`Promoted ${entry.guest_name} to table ${table.code}.`);
      analytics.capture(RestaurantOpsEvents.WAITLIST_PROMOTED, { branch_id: branchId, waitlist_id: entry.id });
    } catch (error) {
      setActionError(getErrorMessage(error, 'Unable to promote waitlist guest.'));
    }
  };

  const createQuickOrder = async () => {
    if (!hasBranchAssignment) {
      setQuickOrderError('Please select an assigned branch before creating a quick order.');
      return;
    }
    if (!hasEligibleStaffContext) {
      setQuickOrderError('Quick order requires an eligible staff context tied to your user account.');
      return;
    }

    const table = tables.data?.find((row) => row.status === 'occupied') ?? null;
    const fallbackMenuId = menuItems.data?.find((row) => row.is_available)?.id ?? null;
    const parsedMenuId = Number(menuItemId || fallbackMenuId);
    if (!Number.isFinite(parsedMenuId) || parsedMenuId <= 0) {
      setQuickOrderError('Choose a valid menu item to create a quick order.');
      return;
    }

    setQuickOrderError(null);
    setActionError(null);
    setActionSuccess(null);
    try {
      await createOrder.mutateAsync({
        branch_id: branchId,
        table_id: table?.id ?? null,
        waiter_id: staffContext.staffId ?? undefined,
        menu_item_id: parsedMenuId,
        quantity: 1,
      });
      setActionSuccess('Quick order created.');
      analytics.capture(RestaurantOpsEvents.QUICK_ORDER_CREATED, { branch_id: branchId, menu_item_id: parsedMenuId });
    } catch (error) {
      setActionError(getErrorMessage(error, 'Unable to create quick order.'));
    }
  };

  const submitReservation = async () => {
    if (!hasBranchAssignment) {
      setFormError('Please select an assigned branch before creating a reservation.');
      return;
    }

    const trimmedGuestName = guestName.trim();
    const trimmedGuestPhone = guestPhone.trim();
    const parsedPartySize = Number(partySize);

    if (!trimmedGuestName) {
      setFormError('Guest name is required.');
      return;
    }
    if (!trimmedGuestPhone) {
      setFormError('Guest phone is required.');
      return;
    }
    if (!Number.isFinite(parsedPartySize) || parsedPartySize < 1) {
      setFormError('Party size must be at least 1.');
      return;
    }

    setFormError(null);
    setActionError(null);
    setActionSuccess(null);

    try {
      await createReservation.mutateAsync({
        branch_id: branchId,
        guest_name: trimmedGuestName,
        guest_phone: trimmedGuestPhone,
        party_size: parsedPartySize,
        reservation_time: new Date(Date.now() + 30 * 60_000).toISOString(),
        notes: 'Created from restaurant operations dashboard',
      });
      analytics.capture(RestaurantOpsEvents.RESERVATION_CREATED, { branch_id: branchId, party_size: parsedPartySize });
      setActionSuccess('Reservation created.');
      setGuestName('');
      setGuestPhone('');
      setPartySize('');
    } catch (error) {
      setActionError(getErrorMessage(error, 'Unable to create reservation.'));
    }
  };

  const advanceTicket = async (ticketId: number, status: KitchenTicketStatus) => {
    const next = nextTicketStatus(status);
    if (!next) return;

    setActionError(null);
    setActionSuccess(null);
    try {
      await updateTicket.mutateAsync({ ticketId, status: next, updatedBy: staffContext.staffId });
      setActionSuccess(`Ticket ${ticketId} moved to ${next}.`);
    } catch (error) {
      setActionError(getErrorMessage(error, `Unable to move ticket ${ticketId}.`));
    }
  };

  const requestCancelApproval = async (orderId: number) => {
    if (!staffContext.staffId) {
      setActionError('Staff context is required to request approval.');
      return;
    }

    setActionError(null);
    setActionSuccess(null);
    try {
      const approval = await createEditApproval.mutateAsync({
        order_id: orderId,
        requested_by: staffContext.staffId,
        reason: 'Cancel requested from dashboard',
      });
      await resolveApproval.mutateAsync({ approvalId: approval.id, status: 'approved', approved_by: staffContext.staffId });
      setApprovalByOrder((prev) => ({ ...prev, [orderId]: approval.id }));
      setActionSuccess(`Approval created for order #${orderId}.`);
    } catch (error) {
      setActionError(getErrorMessage(error, 'Unable to request approval.'));
    }
  };

  const cancelOrderWithApproval = async (orderId: number) => {
    const approvalId = approvalByOrder[orderId];
    if (!approvalId) {
      setActionError('Create approval before cancelling this order.');
      return;
    }

    setActionError(null);
    setActionSuccess(null);
    try {
      await updateOrder.mutateAsync({ orderId, branchId, status: 'cancelled', edit_approval_id: approvalId });
      setActionSuccess(`Order #${orderId} cancelled.`);
    } catch (error) {
      setActionError(getErrorMessage(error, 'Unable to cancel order.'));
    }
  };

  const settleFirstOpenBill = async () => {
    const target = bills.data?.find((bill) => bill.status !== 'paid');
    if (!target) {
      setActionError('No unsettled bill available.');
      return;
    }

    const remaining = Math.max(0, Number((target.total_amount - target.paid_amount).toFixed(2)));
    if (remaining <= 0) {
      setActionError('Selected bill has no remaining balance.');
      return;
    }

    setActionError(null);
    setActionSuccess(null);
    try {
      await settleBill.mutateAsync({
        branchId,
        billId: target.id,
        cashierId: staffContext.staffId,
        amount: remaining,
        paymentMethod: 'cash',
      });
      setActionSuccess(`Bill #${target.id} settled.`);
    } catch (error) {
      setActionError(getErrorMessage(error, 'Unable to settle bill.'));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Restaurant Operations</h1>
          <p className="text-gray-500">Live branch operations for FOH, kitchen, inventory and cashier tracking.</p>
        </div>
        <div className="flex items-end gap-2">
          <div className="w-56">
            <label className="text-xs text-gray-500">Branch</label>
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={branchId}
              onChange={(e) => setBranchId(Number(e.target.value))}
              disabled={!branchChoices.length}
            >
              {!branchChoices.length && <option value={0}>No assigned branches available</option>}
              {branchChoices.map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name} (#{branch.id})
                </option>
              ))}
            </select>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              branches.refetch();
              report.refetch();
              orders.refetch();
              waitlist.refetch();
              tables.refetch();
              reservations.refetch();
              kitchen.refetch();
              bills.refetch();
            }}
          >
            Refresh
          </Button>
        </div>
      </div>

      {(branchGuardMessage || staffGuardMessage || actionError || actionSuccess) && (
        <Card className="border-amber-300 bg-amber-50">
          <CardContent className="pt-6 space-y-2 text-sm text-amber-900">
            {branchGuardMessage && <p>{branchGuardMessage}</p>}
            {staffGuardMessage && <p>{staffGuardMessage}</p>}
            {actionError && <p className="text-red-700">{actionError}</p>}
            {actionSuccess && <p className="text-emerald-700">{actionSuccess}</p>}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card><CardHeader><CardTitle className="text-sm">Orders</CardTitle></CardHeader><CardContent className="text-2xl font-bold">{report.data?.orders_count ?? 0}</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Open Kitchen Tickets</CardTitle></CardHeader><CardContent className="text-2xl font-bold">{report.data?.open_tickets ?? 0}</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Gross Sales</CardTitle></CardHeader><CardContent className="text-2xl font-bold">${(report.data?.gross_sales ?? 0).toFixed(2)}</CardContent></Card>
        <Card><CardHeader><CardTitle className="text-sm">Low Stock Alerts</CardTitle></CardHeader><CardContent className="text-2xl font-bold">{report.data?.low_stock_count ?? 0}</CardContent></Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader><CardTitle>Create Reservation</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <p className="text-xs text-gray-500">Enter guest details to create a reservation.</p>
            <Input value={guestName} onChange={(e) => setGuestName(e.target.value)} placeholder="Guest name" />
            <Input value={guestPhone} onChange={(e) => setGuestPhone(e.target.value)} placeholder="Guest phone" />
            <Input value={partySize} onChange={(e) => setPartySize(e.target.value)} placeholder="Party size" />
            {formError && <p className="text-xs text-red-600">{formError}</p>}
            <Button onClick={submitReservation} disabled={createReservation.isPending || !hasBranchAssignment}>Create Reservation</Button>
            <Button variant="outline" onClick={seatFirstTable} disabled={seatTable.isPending || !hasBranchAssignment}>Seat First Available Table</Button>
            <Button variant="outline" onClick={promoteFirstWaitlist} disabled={promoteWaitlist.isPending || !hasBranchAssignment}>Promote First Waitlist</Button>
            <Input value={menuItemId} onChange={(e) => setMenuItemId(e.target.value)} placeholder="Menu item ID for quick order" list="menu-item-options" />
            <datalist id="menu-item-options">
              {menuItems.data?.map((item) => (
                <option key={item.id} value={String(item.id)}>{item.name} (${item.price.toFixed(2)})</option>
              ))}
            </datalist>
            {quickOrderError && <p className="text-xs text-red-600">{quickOrderError}</p>}
            <Button variant="outline" onClick={createQuickOrder} disabled={createOrder.isPending || !hasBranchAssignment || !hasEligibleStaffContext}>Create Quick Order</Button>
            <Button variant="outline" onClick={settleFirstOpenBill} disabled={settleBill.isPending || !hasBranchAssignment}>Settle First Open Bill</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Tables</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-72 overflow-auto">
            {tables.data?.map((table) => (
              <div key={table.id} className="flex justify-between text-sm border rounded p-2">
                <span>{table.code}</span>
                <span className="text-gray-500">{table.status}</span>
              </div>
            )) ?? <p className="text-sm text-gray-500">No table data</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Waitlist</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-72 overflow-auto">
            {waitlist.data?.items?.map((entry) => (
              <div key={entry.id} className="text-sm border rounded p-2">
                <div className="font-medium">{entry.guest_name}</div>
                <div className="text-gray-500">Party {entry.party_size} · {entry.status}</div>
              </div>
            )) ?? <p className="text-sm text-gray-500">No waitlist entries</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Recent Reservations</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-72 overflow-auto">
            {reservations.data?.map((reservation) => (
              <div key={reservation.id} className="text-sm border rounded p-2">
                <div className="font-medium">{reservation.guest_name}</div>
                <div className="text-gray-500">Party {reservation.party_size} · {reservation.status}</div>
              </div>
            )) ?? <p className="text-sm text-gray-500">No reservations yet</p>}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Recent Orders</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-auto">
            {orders.data?.items?.map((order) => (
              <div key={order.id} className="text-sm border rounded p-2 space-y-2">
                <div className="flex justify-between">
                  <span>Order #{order.id}</span>
                  <span className="text-gray-500">{order.status}</span>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => requestCancelApproval(order.id)} disabled={!hasEligibleStaffContext}>Request Cancel Approval</Button>
                  <Button size="sm" variant="outline" onClick={() => cancelOrderWithApproval(order.id)} disabled={!approvalByOrder[order.id]}>Cancel Order</Button>
                </div>
              </div>
            )) ?? <p className="text-sm text-gray-500">No orders yet</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Kitchen Queue</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-auto">
            {kitchen.data?.items?.map((ticket) => {
              const next = nextTicketStatus(ticket.status);
              return (
                <div key={ticket.id} className="text-sm border rounded p-2 space-y-2">
                  <div className="flex justify-between">
                    <span>Ticket #{ticket.id}</span>
                    <span className="text-gray-500">{ticket.status}</span>
                  </div>
                  {next && (
                    <Button size="sm" variant="outline" onClick={() => advanceTicket(ticket.id, ticket.status)}>
                      Move to {next}
                    </Button>
                  )}
                </div>
              );
            }) ?? <p className="text-sm text-gray-500">No tickets available</p>}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Settlement Health</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>Open drawers: <strong>{report.data?.settlement_health?.open_drawers ?? 0}</strong></div>
            <div>Unpaid bills: <strong>{report.data?.settlement_health?.unpaid_bills ?? 0}</strong></div>
            <div>Failed exports: <strong>{report.data?.settlement_health?.failed_exports ?? 0}</strong></div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Operational Notifications</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-72 overflow-auto">
            {notifications.data?.map((notice) => (
              <div key={notice.id} className="text-sm border rounded p-2">
                <div className="font-medium">{notice.event_name}</div>
                <div className="text-gray-500">{notice.severity} · {new Date(notice.occurred_at).toLocaleString()}</div>
              </div>
            )) ?? <p className="text-sm text-gray-500">No operational notifications</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
