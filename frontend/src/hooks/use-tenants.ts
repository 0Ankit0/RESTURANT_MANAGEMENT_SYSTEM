'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { analytics } from '@/lib/analytics';
import { TenantEvents } from '@/lib/analytics/events';
import type {
  Tenant,
  TenantWithMembers,
  TenantCreate,
  TenantUpdate,
  TenantMember,
  TenantInvitation,
  TenantInvitationCreate,
  TenantRole,
  PaginatedResponse,
} from '@/types';

interface TenantsResponse {
  items: Tenant[];
  total: number;
  skip: number;
  limit: number;
}

export function useTenants(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['tenants', params],
    queryFn: async () => {
      const response = await apiClient.get<TenantsResponse>('/tenants/', { params });
      return response.data;
    },
  });
}

export function useTenant(id: string) {
  return useQuery({
    queryKey: ['tenants', id],
    queryFn: async () => {
      const response = await apiClient.get<TenantWithMembers>(`/tenants/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TenantCreate) => {
      const response = await apiClient.post<Tenant>('/tenants/', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      analytics.capture(TenantEvents.TENANT_CREATED, { name: data.name });
      analytics.group('organization', data.id, { name: data.name });
    },
  });
}

export function useUpdateTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TenantUpdate }) => {
      const response = await apiClient.patch<Tenant>(`/tenants/${id}`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      queryClient.invalidateQueries({ queryKey: ['tenants', variables.id] });
    },
  });
}

export function useDeleteTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/tenants/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
    },
  });
}

export function useTenantMembers(tenantId: string, params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['tenants', tenantId, 'members', params],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<TenantMember>>(
        `/tenants/${tenantId}/members`,
        { params }
      );
      return response.data;
    },
    enabled: !!tenantId,
  });
}

export function useUpdateMemberRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      tenantId,
      userId,
      role,
    }: {
      tenantId: string;
      userId: string;
      role: TenantRole;
    }) => {
      const response = await apiClient.patch<TenantMember>(
        `/tenants/${tenantId}/members/${userId}`,
        { role }
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tenants', variables.tenantId, 'members'] });
    },
  });
}

export function useRemoveMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ tenantId, userId }: { tenantId: string; userId: string }) => {
      await apiClient.delete(`/tenants/${tenantId}/members/${userId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tenants', variables.tenantId, 'members'] });
    },
  });
}

export function useTenantInvitations(tenantId: string, params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['tenants', tenantId, 'invitations', params],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<TenantInvitation>>(
        `/tenants/${tenantId}/invitations`,
        { params }
      );
      return response.data;
    },
    enabled: !!tenantId,
  });
}

export function useCreateInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      tenantId,
      data,
    }: {
      tenantId: string;
      data: TenantInvitationCreate;
    }) => {
      const response = await apiClient.post<TenantInvitation>(
        `/tenants/${tenantId}/invitations`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tenants', variables.tenantId, 'invitations'] });
      analytics.capture(TenantEvents.TENANT_MEMBER_INVITED, { tenant_id: variables.tenantId });
    },
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (token: string) => {
      const response = await apiClient.post('/tenants/invitations/accept', { token });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      analytics.capture(TenantEvents.TENANT_MEMBER_JOINED);
    },
  });
}

export function useDeleteInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      tenantId,
      invitationId,
    }: {
      tenantId: string;
      invitationId: string;
    }) => {
      await apiClient.delete(`/tenants/${tenantId}/invitations/${invitationId}`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tenants', variables.tenantId, 'invitations'] });
    },
  });
}

export function useSwitchTenant() {
  const { setTenant } = useAuthStore();

  return useMutation({
    mutationFn: async (tenant: Tenant) => {
      setTenant(tenant);
      return tenant;
    },
    onSuccess: (tenant) => {
      analytics.group('organization', tenant.id, { name: tenant.name });
    },
  });
}
