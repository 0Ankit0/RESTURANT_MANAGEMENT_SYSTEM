'use client';

import { useState } from 'react';
import { useUserRoles, useAssignRole, useRemoveRole, useEffectivePermissions } from '@/hooks/use-rbac';
import { Card, CardContent } from '@/components/ui/card';
import { Button, Skeleton } from '@/components/ui';
import { Plus, X } from 'lucide-react';
import type { Role } from '@/types';

export function UserRolesTab() {
  const [userId, setUserId] = useState('');
  const [activeUserId, setActiveUserId] = useState('');
  const [roleId, setRoleId] = useState('');
  const [organizationSlug, setOrganizationSlug] = useState('');
  const [branchId, setBranchId] = useState('');
  const { data, isLoading } = useUserRoles(activeUserId);
  const { data: effectivePermissions, isLoading: effectivePermissionsLoading } = useEffectivePermissions(activeUserId, {
    organizationSlug: organizationSlug.trim() || undefined,
    branchId: branchId ? Number(branchId) : undefined,
  });
  const assignRole = useAssignRole();
  const removeRole = useRemoveRole();

  const roles = data?.roles ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Look up a user's roles</p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="User ID (hashid)"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
            <Button onClick={() => setActiveUserId(userId.trim())} disabled={!userId.trim()}>
              Look up
            </Button>
          </div>
        </CardContent>
      </Card>

      {activeUserId && (
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs text-gray-500 mb-2">
              User: <code className="bg-gray-100 px-1 rounded">{activeUserId}</code>
            </p>
            {isLoading && <Skeleton className="h-8 w-full" />}
            <div className="flex flex-wrap gap-2 mb-3">
              {roles.map((role: Role) => (
                <span
                  key={role.id}
                  className="inline-flex items-center gap-1 rounded-full bg-purple-100 text-purple-700 text-sm px-3 py-1"
                >
                  {role.name}
                  <button
                    onClick={() => removeRole.mutate({ user_id: activeUserId, role_id: role.id })}
                    className="ml-0.5 hover:text-red-600"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </span>
              ))}
              {!isLoading && roles.length === 0 && (
                <p className="text-sm text-gray-400">No roles assigned to this user.</p>
              )}
            </div>
            <div className="flex gap-2 items-center border-t border-gray-100 pt-3">
              <input
                type="text"
                placeholder="Role ID to assign"
                value={roleId}
                onChange={(e) => setRoleId(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-48"
              />
              <Button
                size="sm"
                onClick={() => {
                  if (!roleId.trim()) return;
                  assignRole.mutate(
                    { user_id: activeUserId, role_id: roleId.trim() },
                    { onSuccess: () => setRoleId('') }
                  );
                }}
                disabled={assignRole.isPending}
              >
                <Plus className="h-3.5 w-3.5 mr-1" /> Assign Role
              </Button>
            </div>
            <div className="mt-4 space-y-3 border-t border-gray-100 pt-3">
              <p className="text-sm font-medium text-gray-700">Effective permissions (tenant / branch scope)</p>
              <div className="flex flex-wrap gap-2">
                <input
                  type="text"
                  placeholder="Tenant slug (optional)"
                  value={organizationSlug}
                  onChange={(e) => setOrganizationSlug(e.target.value)}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
                <input
                  type="number"
                  placeholder="Branch ID (optional)"
                  value={branchId}
                  onChange={(e) => setBranchId(e.target.value)}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm w-40"
                />
              </div>
              {effectivePermissionsLoading && <Skeleton className="h-8 w-full" />}
              {!effectivePermissionsLoading && (
                <div className="space-y-2">
                  {(effectivePermissions?.permissions ?? []).map((permission) => (
                    <div key={`${permission.domain}:${permission.resource}:${permission.action}:${permission.source}`} className="rounded-md border border-gray-200 px-3 py-2 text-xs">
                      <span className="font-mono">{permission.resource}:{permission.action}</span>
                      <span className="ml-2 text-gray-500">domain={permission.domain}</span>
                      <span className="ml-2 text-gray-500">source={permission.source}</span>
                    </div>
                  ))}
                  {(effectivePermissions?.permissions ?? []).length === 0 && (
                    <p className="text-xs text-gray-400">No effective permissions found in this scope.</p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
