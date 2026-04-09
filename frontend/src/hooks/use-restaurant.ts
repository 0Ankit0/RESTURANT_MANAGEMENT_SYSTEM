'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  BranchOperationsReport,
  RestaurantBranch,
  CursorPage,
  KitchenTicket,
  MenuItem,
  OperationalNotification,
  Reservation,
  RestaurantOrder,
  RestaurantTable,
  WaitlistEntry,
} from '@/types/restaurant';



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
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'waitlist', data.branch_id] });
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'tables', data.branch_id] });
    },
  });
}


export function useSeatTable() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { tableId: number; reservationId?: number; partySize: number }) => {
      const response = await apiClient.post(`/tables/${payload.tableId}/seat`, {
        reservation_id: payload.reservationId,
        party_size: payload.partySize,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant'] });
    },
  });
}

export function usePromoteWaitlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { waitlistId: number; tableId: number }) => {
      const response = await apiClient.patch(`/waitlist/${payload.waitlistId}/promote`, null, {
        params: { table_id: payload.tableId },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant'] });
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
      const response = await apiClient.post('/orders', {
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant'] });
    },
  });
}
