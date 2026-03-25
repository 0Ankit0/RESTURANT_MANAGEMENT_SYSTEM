'use client';

import { useState } from 'react';
import {
  useTenants,
  useCreateTenant,
  useUpdateTenant,
  useDeleteTenant,
  useSwitchTenant,
  useTenantMembers,
  useUpdateMemberRole,
  useRemoveMember,
  useTenantInvitations,
  useCreateInvitation,
  useDeleteInvitation,
} from '@/hooks/use-tenants';
import { useAuthStore } from '@/store/auth-store';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui';
import {
  Building2, Plus, Check, Users, Mail, Pencil, Trash2,
  ChevronDown, ChevronRight, UserMinus, Send, X,
} from 'lucide-react';
import type { Tenant, TenantRole } from '@/types';

const ROLES: TenantRole[] = ['owner', 'admin', 'member'];

function TenantMembersTab({ tenantId }: { tenantId: string }) {
  const { data, isLoading } = useTenantMembers(tenantId);
  const updateRole = useUpdateMemberRole();
  const removeMember = useRemoveMember();
  const members = data?.items ?? [];

  return (
    <div className="mt-3 space-y-2">
      {isLoading && <Skeleton className="h-10 w-full" />}
      {members.length === 0 && !isLoading && (
        <p className="text-sm text-gray-400">No members found.</p>
      )}
      {members.map((m) => (
        <div key={m.user_id} className="flex items-center justify-between bg-white rounded-lg border border-gray-100 px-3 py-2">
          <div>
            <p className="text-sm font-medium text-gray-900">{m.user_id}</p>
            <p className="text-xs text-gray-400 capitalize">{m.role}</p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={m.role}
              onChange={(e) =>
                updateRole.mutate({ tenantId, userId: m.user_id, role: e.target.value as TenantRole })
              }
              className="text-xs border border-gray-200 rounded px-1 py-0.5"
            >
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            <button
              onClick={() => removeMember.mutate({ tenantId, userId: m.user_id })}
              className="text-red-400 hover:text-red-600"
              title="Remove member"
            >
              <UserMinus className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function TenantInvitationsTab({ tenantId }: { tenantId: string }) {
  const { data, isLoading } = useTenantInvitations(tenantId);
  const createInvite = useCreateInvitation();
  const deleteInvite = useDeleteInvitation();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<TenantRole>('member');
  const invitations = data?.items ?? [];

  const handleInvite = () => {
    if (!email.trim()) return;
    createInvite.mutate(
      { tenantId, data: { email, role } },
      { onSuccess: () => setEmail('') }
    );
  };

  return (
    <div className="mt-3 space-y-3">
      <div className="flex gap-2">
        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1 rounded border border-gray-200 px-2 py-1 text-sm"
        />
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as TenantRole)}
          className="border border-gray-200 rounded px-2 py-1 text-sm"
        >
          {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        <Button size="sm" onClick={handleInvite} disabled={createInvite.isPending}>
          <Send className="h-3 w-3 mr-1" /> Invite
        </Button>
      </div>
      {isLoading && <Skeleton className="h-10 w-full" />}
      {invitations.length === 0 && !isLoading && (
        <p className="text-sm text-gray-400">No pending invitations.</p>
      )}
      {invitations.map((inv) => (
        <div key={inv.id} className="flex items-center justify-between bg-white rounded-lg border border-gray-100 px-3 py-2">
          <div>
            <p className="text-sm font-medium text-gray-900">{inv.email}</p>
            <p className="text-xs text-gray-400 capitalize">{inv.role} · {inv.status}</p>
          </div>
          <button
            onClick={() => deleteInvite.mutate({ tenantId, invitationId: inv.id })}
            className="text-red-400 hover:text-red-600"
            title="Cancel invitation"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

function TenantCard({ tenant, isActive }: { tenant: Tenant; isActive: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'members' | 'invitations'>('members');
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState(tenant.name);
  const [editDesc, setEditDesc] = useState(tenant.description ?? '');
  const switchTenant = useSwitchTenant();
  const updateTenant = useUpdateTenant();
  const deleteTenant = useDeleteTenant();

  const handleSave = () => {
    updateTenant.mutate(
      { id: tenant.id, data: { name: editName, description: editDesc } },
      { onSuccess: () => setEditing(false) }
    );
  };

  return (
    <Card className={`transition-all ${isActive ? 'ring-2 ring-blue-500' : ''}`}>
      <CardContent className="pt-4 pb-3">
        {editing ? (
          <div className="space-y-2">
            <input
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
              placeholder="Name"
            />
            <input
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
              placeholder="Description"
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSave} disabled={updateTenant.isPending}>Save</Button>
              <Button size="sm" variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-start justify-between">
              <div
                className="flex items-center gap-3 flex-1 cursor-pointer"
                onClick={() => switchTenant.mutate(tenant)}
              >
                <div className="h-10 w-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <Building2 className="h-5 w-5 text-blue-600" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-gray-900 truncate">{tenant.name}</p>
                  <p className="text-xs text-gray-400">{tenant.slug}</p>
                </div>
              </div>
              <div className="flex items-center gap-1 ml-2">
                {isActive && (
                  <div className="h-5 w-5 rounded-full bg-blue-600 flex items-center justify-center">
                    <Check className="h-3 w-3 text-white" />
                  </div>
                )}
                <button
                  onClick={() => setEditing(true)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  title="Edit"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete "${tenant.name}"?`)) deleteTenant.mutate(tenant.id);
                  }}
                  className="p-1 text-red-400 hover:text-red-600 rounded"
                  title="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setExpanded((v) => !v)}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  title="Manage"
                >
                  {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </button>
              </div>
            </div>
          </>
        )}

        {expanded && !editing && (
          <div className="mt-3 border-t border-gray-100 pt-3">
            <div className="flex gap-3 mb-2">
              {(['members', 'invitations'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded transition-colors ${
                    activeTab === tab ? 'bg-blue-50 text-blue-600' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab === 'members' ? <Users className="h-3 w-3" /> : <Mail className="h-3 w-3" />}
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
            {activeTab === 'members' && <TenantMembersTab tenantId={tenant.id} />}
            {activeTab === 'invitations' && <TenantInvitationsTab tenantId={tenant.id} />}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function TenantsPage() {
  const { data, isLoading } = useTenants();
  const createTenant = useCreateTenant();
  const { tenant: currentTenant } = useAuthStore();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newSlug, setNewSlug] = useState('');
  const [newDesc, setNewDesc] = useState('');

  const handleCreate = async () => {
    if (!newName.trim() || !newSlug.trim()) return;
    await createTenant.mutateAsync(
      { name: newName, slug: newSlug, description: newDesc || undefined },
      {
        onSuccess: () => {
          setNewName(''); setNewSlug(''); setNewDesc('');
          setShowCreateForm(false);
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-28 w-full rounded-xl" />)}
        </div>
      </div>
    );
  }

  const tenants = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
          <p className="text-gray-500">Manage your organizations and teams</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="h-4 w-4 mr-2" /> New Organization
        </Button>
      </div>

      {showCreateForm && (
        <Card>
          <CardHeader><CardTitle>Create Organization</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Input
                placeholder="Name"
                value={newName}
                onChange={(e) => {
                  setNewName(e.target.value);
                  setNewSlug(e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''));
                }}
              />
              <Input
                placeholder="Slug"
                value={newSlug}
                onChange={(e) => setNewSlug(e.target.value)}
              />
              <Input
                placeholder="Description (optional)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
              />
            </div>
            <div className="flex gap-2 mt-3">
              <Button onClick={handleCreate} isLoading={createTenant.isPending}>Create</Button>
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {tenants.length === 0 ? (
        <div className="text-center py-16">
          <Building2 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No organizations yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tenants.map((tenant) => (
            <TenantCard key={tenant.id} tenant={tenant} isActive={currentTenant?.id === tenant.id} />
          ))}
        </div>
      )}
    </div>
  );
}
