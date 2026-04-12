'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  Bill,
  BranchOperationsReport,
  CursorPage,
  KitchenTicket,
  KitchenTicketStatus,
  MenuItem,
  OperationalNotification,
  OrderEditApproval,
  Reservation,
  RestaurantBranch,
  RestaurantOrder,
  RestaurantTable,
  WaitlistEntry,
} from '@/types/restaurant';

type SeatTableResponse = {
  table_id: number;
  status: string;
  party_size: number;
};

const branchQueryKeys = (branchId: number) => [
  ['restaurant', 'tables', branchId],
  ['restaurant', 'orders', branchId],
  ['restaurant', 'waitlist', branchId],
  ['restaurant', 'reservations', branchId],
  ['restaurant', 'branch-report', branchId],
  ['restaurant', 'bills', branchId],
] as const;

function invalidateBranchQueries(queryClient: ReturnType<typeof useQueryClient>, branchId: number) {
  branchQueryKeys(branchId).forEach((queryKey) => {
    queryClient.invalidateQueries({ queryKey });
  });
}

export function useRestaurantBranches() {
  return useQuery({
    queryKey: ['restaurant', 'branches'],
    queryFn: async () => {
      const response = await apiClient.get<RestaurantBranch[]>('/branches');
      return response.data;
    },
  });
}

export function useBranchTables(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'tables', branchId],
    queryFn: async () => {
      const response = await apiClient.get<RestaurantTable[]>(`/branches/${branchId}/tables`);
      return response.data;
    },
    enabled: branchId > 0,
  });
}

export function useBranchOrders(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'orders', branchId],
    queryFn: async () => {
      const response = await apiClient.get<CursorPage<RestaurantOrder>>('/orders', { params: { branch_id: branchId } });
      return response.data;
    },
    enabled: branchId > 0,
  });
}

export function useBranchWaitlist(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'waitlist', branchId],
    queryFn: async () => {
      const response = await apiClient.get<CursorPage<WaitlistEntry>>('/waitlist', { params: { branch_id: branchId } });
      return response.data;
    },
    enabled: branchId > 0,
  });
}

export function useKitchenTickets() {
  return useQuery({
    queryKey: ['restaurant', 'kitchen-tickets'],
    queryFn: async () => {
      const response = await apiClient.get<CursorPage<KitchenTicket>>('/kitchen/tickets');
      return response.data;
    },
  });
}

export function useBranchOperationsReport(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'branch-report', branchId],
    queryFn: async () => {
      const response = await apiClient.get<BranchOperationsReport>('/reports/branch-operations', {
        params: { branch_id: branchId },
      });
      return response.data;
    },
    enabled: branchId > 0,
    refetchInterval: 30_000,
  });
}

export function useOperationalNotifications(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'operational-notifications', branchId],
    queryFn: async () => {
      const response = await apiClient.get<OperationalNotification[]>('/operations/notifications', {
        params: { branch_id: branchId, limit: 20 },
      });
      return response.data;
    },
    enabled: branchId > 0,
    refetchInterval: 30_000,
  });
}

export function useBranchMenuItems(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'menu-items', branchId],
    queryFn: async () => {
      const response = await apiClient.get<MenuItem[]>('/menu-items', { params: { branch_id: branchId } });
      return response.data;
    },
    enabled: branchId > 0,
  });
}

export function useBranchReservations(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'reservations', branchId],
    queryFn: async () => {
      const response = await apiClient.get<Reservation[]>('/reservations', { params: { branch_id: branchId } });
      return response.data;
    },
    enabled: branchId > 0,
  });
}

export function useBranchBills(branchId: number) {
  return useQuery({
    queryKey: ['restaurant', 'bills', branchId],
    queryFn: async () => {
      const response = await apiClient.get<Bill[]>('/bills', { params: { branch_id: branchId } });
      return response.data;
    },
    enabled: branchId > 0,
  });
}

export function useCreateReservation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      branch_id: number;
      guest_name: string;
      guest_phone: string;
      party_size: number;
      reservation_time: string;
      notes?: string;
    }) => {
      const response = await apiClient.post<Reservation>('/reservations', payload);
      return response.data;
    },
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: ['restaurant', 'reservations', payload.branch_id] });
      const previous = queryClient.getQueryData<Reservation[]>(['restaurant', 'reservations', payload.branch_id]) ?? [];
      const optimistic: Reservation = {
        id: -Date.now(),
        branch_id: payload.branch_id,
        guest_name: payload.guest_name,
        guest_phone: payload.guest_phone,
        party_size: payload.party_size,
        reservation_time: payload.reservation_time,
        table_id: null,
        status: 'pending',
        notes: payload.notes,
      };
      queryClient.setQueryData<Reservation[]>(['restaurant', 'reservations', payload.branch_id], [optimistic, ...previous]);
      return { previous, branchId: payload.branch_id };
    },
    onError: (_error, _payload, context) => {
      if (context) {
        queryClient.setQueryData(['restaurant', 'reservations', context.branchId], context.previous);
      }
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branch_id);
    },
  });
}

export function useSeatTable() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { branchId: number; tableId: number; reservationId?: number; partySize: number }) => {
      const response = await apiClient.post<SeatTableResponse>(`/tables/${payload.tableId}/seat`, {
        reservation_id: payload.reservationId,
        party_size: payload.partySize,
      });
      return response.data;
    },
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: ['restaurant', 'tables', payload.branchId] });
      const previous = queryClient.getQueryData<RestaurantTable[]>(['restaurant', 'tables', payload.branchId]) ?? [];
      queryClient.setQueryData<RestaurantTable[]>(['restaurant', 'tables', payload.branchId], (current = []) =>
        current.map((table) => (table.id === payload.tableId ? { ...table, status: 'occupied' } : table))
      );
      return { previous, branchId: payload.branchId };
    },
    onError: (_error, _payload, context) => {
      if (context) {
        queryClient.setQueryData(['restaurant', 'tables', context.branchId], context.previous);
      }
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branchId);
    },
  });
}

export function usePromoteWaitlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { branchId: number; waitlistId: number; tableId: number }) => {
      const response = await apiClient.patch<WaitlistEntry>(`/waitlist/${payload.waitlistId}/promote`, null, {
        params: { table_id: payload.tableId },
      });
      return response.data;
    },
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: ['restaurant', 'waitlist', payload.branchId] });
      const previous = queryClient.getQueryData<CursorPage<WaitlistEntry>>(['restaurant', 'waitlist', payload.branchId]);
      queryClient.setQueryData<CursorPage<WaitlistEntry>>(['restaurant', 'waitlist', payload.branchId], (current) => {
        if (!current) return current;
        return {
          ...current,
          items: current.items.map((entry) =>
            entry.id === payload.waitlistId ? { ...entry, status: 'seated' } : entry
          ),
        };
      });
      return { previous, branchId: payload.branchId };
    },
    onError: (_error, _payload, context) => {
      if (context) {
        queryClient.setQueryData(['restaurant', 'waitlist', context.branchId], context.previous);
      }
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branchId);
    },
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      branch_id: number;
      table_id: number | null;
      waiter_id?: number;
      menu_item_id: number;
      quantity?: number;
    }) => {
      const response = await apiClient.post<{ order: RestaurantOrder; bill: Bill }>('/orders', {
        branch_id: payload.branch_id,
        order_source: 'dine_in',
        table_id: payload.table_id,
        waiter_id: payload.waiter_id ?? null,
        items: [
          {
            menu_item_id: payload.menu_item_id,
            quantity: payload.quantity ?? 1,
            course_no: 1,
          },
        ],
      });
      return response.data;
    },
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: ['restaurant', 'orders', payload.branch_id] });
      const previous = queryClient.getQueryData<CursorPage<RestaurantOrder>>(['restaurant', 'orders', payload.branch_id]);
      const optimisticOrder: RestaurantOrder = {
        id: -Date.now(),
        branch_id: payload.branch_id,
        table_id: payload.table_id,
        waiter_id: payload.waiter_id ?? null,
        order_source: 'dine_in',
        status: 'submitted',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      queryClient.setQueryData<CursorPage<RestaurantOrder>>(['restaurant', 'orders', payload.branch_id], (current) => ({
        items: [optimisticOrder, ...(current?.items ?? [])],
        next_cursor: current?.next_cursor ?? null,
      }));
      return { previous, branchId: payload.branch_id };
    },
    onError: (_error, _payload, context) => {
      if (context) {
        queryClient.setQueryData(['restaurant', 'orders', context.branchId], context.previous);
      }
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branch_id);
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'kitchen-tickets'] });
    },
  });
}

export function useUpdateKitchenTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { ticketId: number; status: KitchenTicketStatus; updatedBy?: number | null }) => {
      const response = await apiClient.patch<KitchenTicket>(`/kitchen/tickets/${payload.ticketId}`, {
        status: payload.status,
        updated_by: payload.updatedBy ?? null,
      });
      return response.data;
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'kitchen-tickets'] });
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'branch-report'] });
    },
  });
}

export function useCreateOrderEditApproval() {
  return useMutation({
    mutationFn: async (payload: { order_id: number; requested_by: number; reason: string }) => {
      const response = await apiClient.post<OrderEditApproval>('/orders/edit-approvals', payload);
      return response.data;
    },
  });
}

export function useResolveOrderEditApproval() {
  return useMutation({
    mutationFn: async (payload: { approvalId: number; status: 'approved' | 'rejected'; approved_by?: number | null }) => {
      const response = await apiClient.patch<OrderEditApproval>(`/orders/edit-approvals/${payload.approvalId}`, {
        status: payload.status,
        approved_by: payload.approved_by ?? null,
      });
      return response.data;
    },
  });
}

export function useUpdateOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      orderId: number;
      branchId: number;
      status?: RestaurantOrder['status'];
      edit_approval_id?: number;
    }) => {
      const response = await apiClient.patch<RestaurantOrder>(`/orders/${payload.orderId}`, {
        status: payload.status,
        edit_approval_id: payload.edit_approval_id,
      });
      return response.data;
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branchId);
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'kitchen-tickets'] });
    },
  });
}

export function useSettleBill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { branchId: number; billId: number; cashierId?: number | null; amount: number; paymentMethod: string }) => {
      const response = await apiClient.post<Bill>(`/bills/${payload.billId}/settlements`, {
        cashier_id: payload.cashierId ?? null,
        settlements: [{ payment_method: payload.paymentMethod, amount: payload.amount }],
      });
      return response.data;
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branchId);
    },
  });
}

export function useCancelReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { branchId: number; reservationId: number }) => {
      const response = await apiClient.post<Reservation>(`/reservations/${payload.reservationId}/cancel`);
      return response.data;
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branchId);
    },
  });
}

export function useTransitionReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { branchId: number; reservationId: number; status: Reservation['status'] }) => {
      const response = await apiClient.patch<Reservation>(`/reservations/${payload.reservationId}`, { status: payload.status });
      return response.data;
    },
    onSettled: (_data, _error, payload) => {
      invalidateBranchQueries(queryClient, payload.branchId);
    },
  });
}
