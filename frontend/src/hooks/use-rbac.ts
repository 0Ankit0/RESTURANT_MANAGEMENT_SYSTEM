'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  Role,
  Permission,
  RoleCreate,
  PermissionCreate,
  RoleAssignment,
  PermissionAssignment,
  UserRolesResponse,
  RolePermissionsResponse,
  CheckPermissionResponse,
  PaginatedResponse,
} from '@/types';

interface AuthorizationScopeOptions {
  organizationId?: string;
  organizationSlug?: string;
  domain?: string;
}

export function useRoles(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['rbac', 'roles', params],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<Role>>('/roles', { params });
      return response.data;
    },
  });
}

export function useRole(roleId: string) {
  return useQuery({
    queryKey: ['rbac', 'roles', roleId],
    queryFn: async () => {
      const response = await apiClient.get<Role>(`/roles/${roleId}`);
      return response.data;
    },
    enabled: !!roleId,
  });
}

export function useCreateRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RoleCreate) => {
      const response = await apiClient.post<Role>('/roles', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'roles'] });
    },
  });
}

export function usePermissions(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['rbac', 'permissions', params],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<Permission>>('/permissions', { params });
      return response.data;
    },
  });
}

export function useCreatePermission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PermissionCreate) => {
      const response = await apiClient.post<Permission>('/permissions', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'permissions'] });
    },
  });
}

export function useUserRoles(userId: string) {
  return useQuery({
    queryKey: ['rbac', 'user-roles', userId],
    queryFn: async () => {
      const response = await apiClient.get<UserRolesResponse>(`/users/${userId}/roles`);
      return response.data;
    },
    enabled: !!userId,
  });
}

export function useAssignRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RoleAssignment) => {
      const response = await apiClient.post('/users/assign-role', data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'user-roles', variables.user_id] });
    },
  });
}

export function useRemoveRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RoleAssignment) => {
      const response = await apiClient.delete('/users/remove-role', { data });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'user-roles', variables.user_id] });
    },
  });
}

export function useRolePermissions(roleId: string) {
  return useQuery({
    queryKey: ['rbac', 'role-permissions', roleId],
    queryFn: async () => {
      const response = await apiClient.get<RolePermissionsResponse>(`/roles/${roleId}/permissions`);
      return response.data;
    },
    enabled: !!roleId,
  });
}

export function useAssignPermission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PermissionAssignment) => {
      const response = await apiClient.post('/roles/assign-permission', data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'role-permissions', variables.role_id] });
    },
  });
}

export function useRemovePermission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PermissionAssignment) => {
      const response = await apiClient.delete('/roles/remove-permission', { data });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'role-permissions', variables.role_id] });
    },
  });
}

export function useCheckPermission(
  userId: string,
  resource: string,
  action: string,
  scope?: AuthorizationScopeOptions
) {
  const resolvedScope = {
    organizationId: scope?.organizationId,
    organizationSlug: scope?.organizationSlug,
    domain: scope?.domain,
  };
  return useQuery({
    queryKey: ['rbac', 'check-permission', userId, resolvedScope, resource, action],
    queryFn: async () => {
      const response = await apiClient.get<CheckPermissionResponse>(
        `/check-permission/${userId}`,
        {
          params: {
            resource,
            action,
            organization_id: resolvedScope.organizationId,
            organization_slug: resolvedScope.organizationSlug,
            domain: resolvedScope.domain,
          },
        }
      );
      return response.data;
    },
    enabled: !!userId && !!resource && !!action,
  });
}

export function useCasbinRoles(userId: string, scope?: AuthorizationScopeOptions) {
  const resolvedScope = {
    organizationId: scope?.organizationId,
    organizationSlug: scope?.organizationSlug,
    domain: scope?.domain,
  };
  return useQuery({
    queryKey: ['rbac', 'casbin-roles', userId, resolvedScope],
    queryFn: async () => {
      const response = await apiClient.get<{ user_id: string; domain: string; roles: string[] }>(
        `/casbin/roles/${userId}`,
        {
          params: {
            organization_id: resolvedScope.organizationId,
            organization_slug: resolvedScope.organizationSlug,
            domain: resolvedScope.domain,
          },
        }
      );
      return response.data;
    },
    enabled: !!userId,
  });
}

export function useCasbinPermissions(userId: string, scope?: AuthorizationScopeOptions) {
  const resolvedScope = {
    organizationId: scope?.organizationId,
    organizationSlug: scope?.organizationSlug,
    domain: scope?.domain,
  };
  return useQuery({
    queryKey: ['rbac', 'casbin-permissions', userId, resolvedScope],
    queryFn: async () => {
      const response = await apiClient.get<{ user_id: string; domain: string; permissions: string[][] }>(
        `/casbin/permissions/${userId}`,
        {
          params: {
            organization_id: resolvedScope.organizationId,
            organization_slug: resolvedScope.organizationSlug,
            domain: resolvedScope.domain,
          },
        }
      );
      return response.data;
    },
    enabled: !!userId,
  });
}
