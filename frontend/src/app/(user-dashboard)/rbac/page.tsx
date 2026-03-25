'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  useRoles,
  usePermissions,
  useCreateRole,
  useCreatePermission,
} from '@/hooks/use-rbac';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui';
import { ShieldCheck, Key, Plus, Settings2 } from 'lucide-react';
import type { Role } from '@/types';

type Tab = 'roles' | 'permissions';

// ── Role row ─────────────────────────────────────────────────────────────────
function RoleRow({ role }: { role: Role }) {
  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="px-4 py-3">
        <span className="text-sm font-medium text-gray-900">{role.name}</span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">{role.description || '—'}</td>
      <td className="px-4 py-3 text-sm text-gray-400">
        {new Date(role.created_at).toLocaleDateString()}
      </td>
      <td className="px-4 py-3 text-right">
        <Link
          href={`/admin/rbac/${role.id}`}
          className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors"
          title="Manage permissions"
        >
          <Settings2 className="h-3.5 w-3.5" />
          Manage
        </Link>
      </td>
    </tr>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function RBACPage() {
  const [activeTab, setActiveTab] = useState<Tab>('roles');

  const rolesQuery = useRoles();
  const permissionsQuery = usePermissions();
  const createRole = useCreateRole();
  const createPermission = useCreatePermission();

  const [showRoleForm, setShowRoleForm] = useState(false);
  const [roleName, setRoleName] = useState('');
  const [roleDesc, setRoleDesc] = useState('');

  const [showPermForm, setShowPermForm] = useState(false);
  const [permResource, setPermResource] = useState('');
  const [permAction, setPermAction] = useState('');
  const [permDesc, setPermDesc] = useState('');

  const handleCreateRole = (e: React.FormEvent) => {
    e.preventDefault();
    createRole.mutate(
      { name: roleName, description: roleDesc },
      { onSuccess: () => { setRoleName(''); setRoleDesc(''); setShowRoleForm(false); } }
    );
  };

  const handleCreatePermission = (e: React.FormEvent) => {
    e.preventDefault();
    createPermission.mutate(
      { resource: permResource, action: permAction, description: permDesc },
      { onSuccess: () => { setPermResource(''); setPermAction(''); setPermDesc(''); setShowPermForm(false); } }
    );
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'roles', label: 'Roles', icon: <ShieldCheck className="h-4 w-4" /> },
    { id: 'permissions', label: 'Permissions', icon: <Key className="h-4 w-4" /> },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Roles & Permissions</h1>
        <p className="text-gray-500">Manage role and permission definitions for the platform</p>
      </div>

      <div className="flex gap-2 border-b border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'roles' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowRoleForm(!showRoleForm)}>
              <Plus className="h-4 w-4 mr-2" /> New Role
            </Button>
          </div>

          {showRoleForm && (
            <Card>
              <CardContent className="pt-4">
                <form onSubmit={handleCreateRole} className="space-y-3">
                  <h3 className="font-semibold text-gray-900">Create Role</h3>
                  <input
                    type="text"
                    placeholder="Role name"
                    value={roleName}
                    onChange={(e) => setRoleName(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Description (optional)"
                    value={roleDesc}
                    onChange={(e) => setRoleDesc(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                  <div className="flex gap-2">
                    <Button type="submit" disabled={createRole.isPending}>
                      {createRole.isPending ? 'Creating…' : 'Create'}
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setShowRoleForm(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rolesQuery.isLoading && (
                  <tr><td colSpan={4} className="px-4 py-4 text-center text-gray-500">Loading…</td></tr>
                )}
                {(rolesQuery.data?.items ?? []).map((role) => (
                  <RoleRow key={role.id} role={role} />
                ))}
                {!rolesQuery.isLoading && rolesQuery.data?.items.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-6 text-center text-gray-500">No roles found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'permissions' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setShowPermForm(!showPermForm)}>
              <Plus className="h-4 w-4 mr-2" /> New Permission
            </Button>
          </div>

          {showPermForm && (
            <Card>
              <CardContent className="pt-4">
                <form onSubmit={handleCreatePermission} className="space-y-3">
                  <h3 className="font-semibold text-gray-900">Create Permission</h3>
                  <input
                    type="text"
                    placeholder="Resource (e.g. users)"
                    value={permResource}
                    onChange={(e) => setPermResource(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Action (e.g. read)"
                    value={permAction}
                    onChange={(e) => setPermAction(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Description (optional)"
                    value={permDesc}
                    onChange={(e) => setPermDesc(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                  <div className="flex gap-2">
                    <Button type="submit" disabled={createPermission.isPending}>
                      {createPermission.isPending ? 'Creating…' : 'Create'}
                    </Button>
                    <Button type="button" variant="outline" onClick={() => setShowPermForm(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {permissionsQuery.isLoading && (
                  <tr><td colSpan={3} className="px-4 py-4 text-center text-gray-500">Loading…</td></tr>
                )}
                {(permissionsQuery.data?.items ?? []).map((perm) => (
                  <tr key={perm.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{perm.resource}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{perm.action}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{perm.description || '—'}</td>
                  </tr>
                ))}
                {!permissionsQuery.isLoading && permissionsQuery.data?.items.length === 0 && (
                  <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-500">No permissions found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
