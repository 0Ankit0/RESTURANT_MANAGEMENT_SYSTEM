'use client';

import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  useBranchOperationsReport,
  useBranchOrders,
  useRestaurantBranches,
  useBranchTables,
  useBranchWaitlist,
  useBranchMenuItems,
  useBranchReservations,
  useCreateOrder,
  useCreateReservation,
  useKitchenTickets,
  useOperationalNotifications,
  usePromoteWaitlist,
  useSeatTable,
} from '@/hooks/use-restaurant';
import { useAnalytics } from '@/hooks/use-analytics';
import { RestaurantOpsEvents } from '@/lib/analytics/events';
import { useAuthStore } from '@/store/auth-store';

type StaffContext = {
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

const deriveStaffContext = (user: unknown): StaffContext => {
  if (!user || typeof user !== 'object') {
    return { staffId: null, branchPreferences: [] };
  }

  const record = user as Record<string, unknown>;
  const defaultBranch = asPositiveNumber(
    record.default_branch_id ?? record.defaultBranchId ?? record.branch_id ?? record.branchId
  );
  const membershipBranches = normalizeBranchPreferences(record.branch_memberships ?? record.branchMemberships ?? record.branches);
  const fallbackBranches = normalizeBranchPreferences(record.assigned_branch_ids ?? record.assignedBranchIds);

  return {
    staffId: asPositiveNumber(record.staff_id ?? record.staffId ?? record.id),
    branchPreferences: [defaultBranch, ...membershipBranches, ...fallbackBranches].filter(
      (entry): entry is number => entry !== null
    ),
  };
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

  const staffContext = useMemo(() => deriveStaffContext(user), [user]);

  const branches = useRestaurantBranches();
  const availableBranchIds = useMemo(() => new Set((branches.data ?? []).map((branch) => branch.id)), [branches.data]);
  const resolvedBranchId = useMemo(() => {
    const preferred = staffContext.branchPreferences.find((candidate) => availableBranchIds.has(candidate));
    return preferred ?? (branches.data?.[0]?.id ?? 0);
  }, [availableBranchIds, branches.data, staffContext.branchPreferences]);

  useEffect(() => {
    if (branchId > 0) return;
    if (!resolvedBranchId) return;
    setBranchId(resolvedBranchId);
  }, [branchId, resolvedBranchId]);

  const tables = useBranchTables(branchId);
  const orders = useBranchOrders(branchId);
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
    ? 'No eligible staff profile is linked to your user. Quick order creation is disabled until staff context is available.'
    : null;


  const seatFirstTable = async () => {
    const table = tables.data?.find((row) => row.status === 'available');
    if (!table) return;
    await seatTable.mutateAsync({ tableId: table.id, partySize: 2 });
  };

  const promoteFirstWaitlist = async () => {
    const entry = waitlist.data?.items?.find((row) => row.status === 'waiting');
    const table = tables.data?.find((row) => row.status === 'available');
    if (!entry || !table) return;
    await promoteWaitlist.mutateAsync({ waitlistId: entry.id, tableId: table.id });
    analytics.capture(RestaurantOpsEvents.WAITLIST_PROMOTED, { branch_id: branchId, waitlist_id: entry.id });
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
    await createOrder.mutateAsync({
      branch_id: branchId,
      table_id: table?.id ?? null,
      waiter_id: staffContext.staffId,
      menu_item_id: parsedMenuId,
      quantity: 1,
    });
    analytics.capture(RestaurantOpsEvents.QUICK_ORDER_CREATED, { branch_id: branchId, menu_item_id: parsedMenuId });
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

    await createReservation.mutateAsync({
      branch_id: branchId,
      guest_name: trimmedGuestName,
      guest_phone: trimmedGuestPhone,
      party_size: parsedPartySize,
      reservation_time: new Date(Date.now() + 30 * 60_000).toISOString(),
      notes: 'Created from restaurant operations dashboard',
    });
    analytics.capture(RestaurantOpsEvents.RESERVATION_CREATED, { branch_id: branchId, party_size: parsedPartySize });

    setGuestName('');
    setGuestPhone('');
    setPartySize('');
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
              disabled={!branches.data?.length}
            >
              {!branches.data?.length && <option value={0}>No branches available</option>}
              {(branches.data ?? []).map((branch) => (
                <option key={branch.id} value={branch.id}>
                  {branch.name} (#{branch.id})
                </option>
              ))}
            </select>
          </div>
          <Button variant="outline" onClick={() => { branches.refetch(); report.refetch(); orders.refetch(); waitlist.refetch(); tables.refetch(); }}>Refresh</Button>
        </div>
      </div>

      {(branchGuardMessage || staffGuardMessage) && (
        <Card className="border-amber-300 bg-amber-50">
          <CardContent className="pt-6 space-y-2 text-sm text-amber-900">
            {branchGuardMessage && <p>{branchGuardMessage}</p>}
            {staffGuardMessage && <p>{staffGuardMessage}</p>}
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <Card>
          <CardHeader><CardTitle className="text-sm">Orders</CardTitle></CardHeader>
          <CardContent className="text-2xl font-bold">{report.data?.orders_count ?? 0}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Open Kitchen Tickets</CardTitle></CardHeader>
          <CardContent className="text-2xl font-bold">{report.data?.open_tickets ?? 0}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Gross Sales</CardTitle></CardHeader>
          <CardContent className="text-2xl font-bold">${(report.data?.gross_sales ?? 0).toFixed(2)}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Low Stock Alerts</CardTitle></CardHeader>
          <CardContent className="text-2xl font-bold">{report.data?.low_stock_count ?? 0}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Service Delays</CardTitle></CardHeader>
          <CardContent className="text-2xl font-bold">{report.data?.service_delay_count ?? 0}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Staffing Gaps</CardTitle></CardHeader>
          <CardContent className="text-2xl font-bold">{report.data?.staffing?.coverage_gap_count ?? 0}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-sm">Ops Exceptions</CardTitle></CardHeader>
          <CardContent className="text-2xl font-bold">{report.data?.operational_exception_count ?? 0}</CardContent>
        </Card>
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
              <div key={order.id} className="text-sm border rounded p-2 flex justify-between">
                <span>Order #{order.id}</span>
                <span className="text-gray-500">{order.status}</span>
              </div>
            )) ?? <p className="text-sm text-gray-500">No orders yet</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Kitchen Queue</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-80 overflow-auto">
            {kitchen.data?.items?.map((ticket) => (
              <div key={ticket.id} className="text-sm border rounded p-2 flex justify-between">
                <span>Ticket #{ticket.id}</span>
                <span className="text-gray-500">{ticket.status}</span>
              </div>
            )) ?? <p className="text-sm text-gray-500">No tickets available</p>}
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
