'use client';

import { useState } from 'react';
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
  usePromoteWaitlist,
  useSeatTable,
} from '@/hooks/use-restaurant';

export default function RestaurantOpsPage() {
  const [branchId, setBranchId] = useState(1);
  const [guestName, setGuestName] = useState('Walk-in Guest');
  const [guestPhone, setGuestPhone] = useState('+10000000000');
  const [partySize, setPartySize] = useState('2');
  const [menuItemId, setMenuItemId] = useState('');

  const branches = useRestaurantBranches();
  const tables = useBranchTables(branchId);
  const orders = useBranchOrders(branchId);
  const waitlist = useBranchWaitlist(branchId);
  const menuItems = useBranchMenuItems(branchId);
  const reservations = useBranchReservations(branchId);
  const kitchen = useKitchenTickets();
  const report = useBranchOperationsReport(branchId);
  const createReservation = useCreateReservation();
  const seatTable = useSeatTable();
  const promoteWaitlist = usePromoteWaitlist();
  const createOrder = useCreateOrder();



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
  };

  const createQuickOrder = async () => {
    const table = tables.data?.find((row) => row.status === 'occupied') ?? null;
    const fallbackMenuId = menuItems.data?.find((row) => row.is_available)?.id ?? null;
    const parsedMenuId = Number(menuItemId || fallbackMenuId);
    if (!Number.isFinite(parsedMenuId) || parsedMenuId <= 0 || branchId <= 0) return;
    await createOrder.mutateAsync({
      branch_id: branchId,
      table_id: table?.id ?? null,
      waiter_id: 1,
      menu_item_id: parsedMenuId,
      quantity: 1,
    });
  };

  const submitReservation = async () => {
    if (branchId <= 0) return;

    await createReservation.mutateAsync({
      branch_id: branchId,
      guest_name: guestName,
      guest_phone: guestPhone,
      party_size: Math.max(1, Number(partySize) || 1),
      reservation_time: new Date(Date.now() + 30 * 60_000).toISOString(),
      notes: 'Created from restaurant operations dashboard',
    });
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
            >
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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader><CardTitle>Create Reservation</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <Input value={guestName} onChange={(e) => setGuestName(e.target.value)} placeholder="Guest name" />
            <Input value={guestPhone} onChange={(e) => setGuestPhone(e.target.value)} placeholder="Guest phone" />
            <Input value={partySize} onChange={(e) => setPartySize(e.target.value)} placeholder="Party size" />
            <Button onClick={submitReservation} disabled={createReservation.isPending}>Create Reservation</Button>
            <Button variant="outline" onClick={seatFirstTable} disabled={seatTable.isPending}>Seat First Available Table</Button>
            <Button variant="outline" onClick={promoteFirstWaitlist} disabled={promoteWaitlist.isPending}>Promote First Waitlist</Button>
            <Input value={menuItemId} onChange={(e) => setMenuItemId(e.target.value)} placeholder="Menu item ID for quick order" list="menu-item-options" />
            <datalist id="menu-item-options">
              {menuItems.data?.map((item) => (
                <option key={item.id} value={String(item.id)}>{item.name} (${item.price.toFixed(2)})</option>
              ))}
            </datalist>
            <Button variant="outline" onClick={createQuickOrder} disabled={createOrder.isPending}>Create Quick Order</Button>
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
    </div>
  );
}
