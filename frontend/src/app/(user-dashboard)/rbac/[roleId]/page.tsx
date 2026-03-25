'use client';

import { useState } from 'react';
import { use } from 'react';
import Link from 'next/link';
import {
  useRole,
  useRolePermissions,
  usePermissions,
  useAssignPermission,
  useRemovePermission,
} from '@/hooks/use-rbac';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button, Skeleton } from '@/components/ui';
import {
  ArrowLeft,
  ShieldCheck,
  Plus,
  X,
  Search,
  CheckCircle2,
} from 'lucide-react';
import type { Permission } from '@/types';

export default function RoleManagePage({
  params,
}: {
  params: Promise<{ roleId: string }>;
}) {
  const { roleId } = use(params);

  const { data: role, isLoading: roleLoading } = useRole(roleId);
  const { data: rolePerms, isLoading: rolePermsLoading } = useRolePermissions(roleId);
  const { data: allPerms, isLoading: allPermsLoading } = usePermissions({ limit: 200 });
  const assignPerm = useAssignPermission();
  const removePerm = useRemovePermission();

  const [search, setSearch] = useState('');

  const assigned = rolePerms?.permissions ?? [];
  const assignedIds = new Set(assigned.map((p) => p.id));

  const available = (allPerms?.items ?? []).filter(
    (p) =>
      !assignedIds.has(p.id) &&
      (search === '' ||
        `${p.resource}:${p.action}`.toLowerCase().includes(search.toLowerCase()) ||
        p.description?.toLowerCase().includes(search.toLowerCase()))
  );

  // Group assigned permissions by resource
  const grouped = assigned.reduce<Record<string, Permission[]>>((acc, p) => {
    (acc[p.resource] ??= []).push(p);
    return acc;
  }, {});

  if (roleLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!role) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <ShieldCheck className="h-12 w-12 text-gray-300" />
        <p className="text-gray-500">Role not found.</p>
        <Link href="/admin/rbac">
          <Button variant="outline" size="sm">Back to Roles</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start gap-4">
        <Link
          href="/admin/rbac"
          className="mt-1 p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">{role.name}</h1>
          </div>
          {role.description && (
            <p className="mt-1 text-sm text-gray-500">{role.description}</p>
          )}
        </div>
        <span className="text-xs text-gray-400 mt-1">ID: {role.id}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Assigned permissions ──────────────────────────────────────── */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              Assigned Permissions
            </CardTitle>
            <span className="text-xs font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
              {assigned.length}
            </span>
          </CardHeader>
          <CardContent>
            {rolePermsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : assigned.length === 0 ? (
              <div className="py-8 text-center">
                <ShieldCheck className="h-8 w-8 text-gray-200 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No permissions assigned yet.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(grouped).map(([resource, perms]) => (
                  <div key={resource}>
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                      {resource}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {perms.map((perm) => (
                        <span
                          key={perm.id}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 text-blue-700 text-xs font-medium px-2.5 py-1.5 border border-blue-100"
                        >
                          <span className="font-mono">{perm.action}</span>
                          {perm.description && (
                            <span className="text-blue-400 hidden sm:inline">· {perm.description}</span>
                          )}
                          <button
                            onClick={() =>
                              removePerm.mutate({ role_id: roleId, permission_id: perm.id })
                            }
                            disabled={removePerm.isPending}
                            className="ml-0.5 text-blue-400 hover:text-red-500 transition-colors disabled:opacity-50"
                            title="Remove permission"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Available permissions ─────────────────────────────────────── */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Plus className="h-4 w-4 text-gray-400" />
              Available Permissions
            </CardTitle>
            <span className="text-xs font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
              {available.length}
            </span>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
              <input
                type="text"
                placeholder="Filter permissions…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-2 text-sm rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {allPermsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
              </div>
            ) : available.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-sm text-gray-400">
                  {search ? 'No matching permissions.' : 'All permissions are already assigned.'}
                </p>
              </div>
            ) : (
              <div className="max-h-96 overflow-y-auto space-y-1 -mx-1 px-1">
                {available.map((perm) => (
                  <div
                    key={perm.id}
                    className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-gray-50 transition-colors group"
                  >
                    <div className="min-w-0">
                      <span className="text-sm font-medium text-gray-900 font-mono">
                        {perm.resource}:{perm.action}
                      </span>
                      {perm.description && (
                        <p className="text-xs text-gray-400 truncate">{perm.description}</p>
                      )}
                    </div>
                    <button
                      onClick={() =>
                        assignPerm.mutate({ role_id: roleId, permission_id: perm.id })
                      }
                      disabled={assignPerm.isPending}
                      className="ml-3 flex-shrink-0 flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-50"
                      title="Assign permission"
                    >
                      <Plus className="h-3 w-3" />
                      Add
                    </button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
