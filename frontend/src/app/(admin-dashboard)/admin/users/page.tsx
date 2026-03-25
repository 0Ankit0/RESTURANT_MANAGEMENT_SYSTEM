'use client';

import { useDeferredValue, useState } from 'react';
import {
  useAssignRole,
  useRemoveRole,
  useRoles,
  useUserRoles,
} from '@/hooks/use-rbac';
import { useDeleteUser, useListUsers, useUpdateUser } from '@/hooks/use-users';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Mail,
  Pencil,
  Search,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  Users,
  X,
} from 'lucide-react';
import type { User } from '@/types';

type ActivityFilter = 'all' | 'active' | 'inactive';

function StatCard({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: number;
  icon: typeof Users;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-500">{label}</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
        </div>
        <div className={`rounded-2xl p-3 ${accent}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

function UserEditor({
  user,
  onClose,
}: {
  user: User;
  onClose: () => void;
}) {
  const updateUser = useUpdateUser();
  const [email, setEmail] = useState(user.email);
  const [firstName, setFirstName] = useState(user.first_name ?? '');
  const [lastName, setLastName] = useState(user.last_name ?? '');
  const [phone, setPhone] = useState(user.phone ?? '');
  const [isActive, setIsActive] = useState(user.is_active);
  const [isSuperuser, setIsSuperuser] = useState(user.is_superuser);
  const { data: availableRolesData } = useRoles({ limit: 200 });
  const { data: userRolesData } = useUserRoles(user.id);
  const assignRole = useAssignRole();
  const removeRole = useRemoveRole();
  const [selectedRoleId, setSelectedRoleId] = useState('');

  const availableRoles = availableRolesData?.items ?? [];
  const assignedRoles = userRolesData?.roles ?? [];
  const assignedRoleIds = new Set(assignedRoles.map((role) => role.id));
  const unassignedRoles = availableRoles.filter((role) => !assignedRoleIds.has(role.id));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 backdrop-blur-sm">
      <div className="w-full max-w-3xl rounded-[28px] border border-white/40 bg-[#fcfbf8] p-6 shadow-[0_16px_40px_rgba(15,23,42,0.12)]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">
              User Controls
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-gray-900">{user.username}</h2>
            <p className="mt-1 text-sm text-gray-500">
              Update profile details, access level, and account state.
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
              Email
            </label>
            <Input value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
              Phone
            </label>
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
              First Name
            </label>
            <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
              Last Name
            </label>
            <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <label className="flex items-center justify-between rounded-2xl border border-gray-200 bg-white p-4">
            <div>
              <p className="text-sm font-medium text-gray-900">Account active</p>
              <p className="text-xs text-gray-500">Controls whether the user can sign in.</p>
            </div>
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
          </label>
          <label className="flex items-center justify-between rounded-2xl border border-gray-200 bg-white p-4">
            <div>
              <p className="text-sm font-medium text-gray-900">Superuser access</p>
              <p className="text-xs text-gray-500">Grants unrestricted admin privileges.</p>
            </div>
            <input
              type="checkbox"
              checked={isSuperuser}
              onChange={(e) => setIsSuperuser(e.target.checked)}
              className="h-4 w-4 rounded border-gray-300"
            />
          </label>
        </div>

        <div className="mt-6 rounded-2xl border border-gray-200 bg-white p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-gray-900">Assigned roles</p>
              <p className="mt-1 text-xs text-gray-500">
                Add or remove RBAC roles for this user directly from the admin dashboard.
              </p>
            </div>
            <ShieldCheck className="h-5 w-5 text-blue-600" />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {assignedRoles.length === 0 ? (
              <span className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-600">
                No roles assigned
              </span>
            ) : (
              assignedRoles.map((role) => (
                <span
                  key={role.id}
                  className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700"
                >
                  {role.name}
                  <button
                    type="button"
                    onClick={() => removeRole.mutate({ user_id: user.id, role_id: role.id })}
                    disabled={removeRole.isPending}
                    className="text-blue-500 transition-colors hover:text-red-600 disabled:opacity-50"
                    aria-label={`Remove ${role.name}`}
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </span>
              ))
            )}
          </div>

          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <select
              value={selectedRoleId}
              onChange={(event) => setSelectedRoleId(event.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a role to assign</option>
              {unassignedRoles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              disabled={!selectedRoleId || assignRole.isPending}
              isLoading={assignRole.isPending}
              onClick={() =>
                assignRole.mutate(
                  { user_id: user.id, role_id: selectedRoleId },
                  { onSuccess: () => setSelectedRoleId('') }
                )
              }
            >
              Assign role
            </Button>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            isLoading={updateUser.isPending}
            onClick={() =>
              updateUser.mutate(
                {
                  userId: user.id,
                  data: {
                    email,
                    first_name: firstName || undefined,
                    last_name: lastName || undefined,
                    phone: phone || undefined,
                    is_active: isActive,
                    is_superuser: isSuperuser,
                  },
                },
                { onSuccess: onClose }
              )
            }
          >
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function AdminUsersPage() {
  const limit = 12;
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const deferredSearch = useDeferredValue(search);
  const [activityFilter, setActivityFilter] = useState<ActivityFilter>('all');
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const deleteUser = useDeleteUser();

  const queryIsActive =
    activityFilter === 'all' ? undefined : activityFilter === 'active';

  const { data, isLoading } = useListUsers({
    skip: page * limit,
    limit,
    search: deferredSearch || undefined,
    is_active: queryIsActive,
  });

  const users = data?.items ?? [];
  const total = data?.total ?? 0;
  const activeCount = users.filter((user) => user.is_active).length;
  const inactiveCount = users.filter((user) => !user.is_active).length;
  const adminCount = users.filter((user) => user.is_superuser).length;

  return (
    <div className="space-y-6">
      <div className="rounded-[32px] border border-[#d8d2c7] bg-[linear-gradient(140deg,#f7f1e8_0%,#fcfbf8_55%,#eef3ff_100%)] p-6 shadow-[0_1px_2px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-gray-500">
              Admin Console
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-gray-900">
              User Management
            </h1>
            <p className="mt-2 max-w-2xl text-sm text-gray-600">
              Review the full user roster, promote trusted operators, and disable compromised accounts
              without leaving the dashboard.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <StatCard label="Active" value={activeCount} icon={Users} accent="bg-blue-50 text-blue-700" />
            <StatCard label="Admins" value={adminCount} icon={Shield} accent="bg-amber-50 text-amber-700" />
            <StatCard label="Inactive" value={inactiveCount} icon={ShieldAlert} accent="bg-rose-50 text-rose-700" />
          </div>
        </div>
      </div>

      <Card className="overflow-hidden rounded-[28px] border-[#e2ddd4]">
        <CardHeader className="border-b border-gray-100 bg-[#fcfbf8]">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <CardTitle className="text-xl">Roster</CardTitle>
              <p className="mt-1 text-sm text-gray-500">{total} users match the current filters.</p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative min-w-[260px]">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <Input
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(0);
                  }}
                  placeholder="Search username or email"
                  className="pl-9"
                />
              </div>
              <div className="flex rounded-2xl border border-gray-200 bg-white p-1">
                {(['all', 'active', 'inactive'] as const).map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => {
                      setActivityFilter(filter);
                      setPage(0);
                    }}
                    className={`rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
                      activityFilter === filter
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {filter[0].toUpperCase() + filter.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[860px]">
              <thead className="bg-[#f8f6f0] text-left">
                <tr>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
                    User
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
                    Contact
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
                    Access
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
                    Verification
                  </th>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, index) => (
                    <tr key={index} className="border-t border-gray-100">
                      <td className="px-5 py-5" colSpan={5}>
                        <div className="h-10 animate-pulse rounded-xl bg-gray-100" />
                      </td>
                    </tr>
                  ))
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-16 text-center">
                      <p className="text-base font-medium text-gray-700">No users found.</p>
                      <p className="mt-1 text-sm text-gray-500">
                        Try a different search term or switch the activity filter.
                      </p>
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id} className="border-t border-gray-100 bg-white">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#eef3ff] font-semibold text-[#275efe]">
                            {(user.first_name?.[0] ?? user.username[0]).toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-gray-900">
                              {user.first_name || user.last_name
                                ? `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim()
                                : user.username}
                            </p>
                            <p className="text-xs text-gray-500">@{user.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <p className="flex items-center gap-2 text-sm text-gray-700">
                          <Mail className="h-3.5 w-3.5 text-gray-400" />
                          {user.email}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">{user.phone || 'No phone number'}</p>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex flex-wrap gap-2">
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                              user.is_active
                                ? 'bg-emerald-50 text-emerald-700'
                                : 'bg-rose-50 text-rose-700'
                            }`}
                          >
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                              user.is_superuser
                                ? 'bg-amber-50 text-amber-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {user.is_superuser ? 'Superuser' : 'Standard'}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2 text-sm">
                          {user.is_confirmed ? (
                            <Check className="h-4 w-4 text-emerald-600" />
                          ) : (
                            <X className="h-4 w-4 text-rose-500" />
                          )}
                          <span className="text-gray-700">
                            {user.is_confirmed ? 'Verified' : 'Pending'}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setEditingUser(user)}
                            title="Edit user"
                            aria-label="Edit user"
                            className="px-2.5"
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setEditingUser(user)}
                            title="Assign role"
                            aria-label="Assign role"
                            className="px-2.5"
                          >
                            <ShieldCheck className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeletingUser(user)}
                            title="Delete user"
                            aria-label="Delete user"
                            className="px-2.5 text-red-600 hover:bg-red-50 hover:text-red-700"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {total > 0 ? (
        <div className="flex items-center justify-between rounded-2xl border border-gray-200 bg-white px-4 py-3">
          <p className="text-sm text-gray-600">
            Showing {Math.min(total, page * limit + 1)}-{Math.min(total, (page + 1) * limit)} of {total}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((current) => Math.max(0, current - 1))}
              disabled={page === 0}
            >
              <ChevronLeft className="mr-1 h-3.5 w-3.5" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((current) => current + 1)}
              disabled={(page + 1) * limit >= total}
            >
              Next
              <ChevronRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      ) : null}

      {editingUser ? <UserEditor user={editingUser} onClose={() => setEditingUser(null)} /> : null}

      <ConfirmDialog
        open={!!deletingUser}
        title={deletingUser ? `Delete ${deletingUser.username}?` : 'Delete user?'}
        description="This removes the user account and related access records. This action cannot be undone."
        confirmLabel="Delete user"
        onCancel={() => setDeletingUser(null)}
        onConfirm={() => {
          if (!deletingUser) return;
          deleteUser.mutate(deletingUser.id, {
            onSuccess: () => setDeletingUser(null),
          });
        }}
        isLoading={deleteUser.isPending}
      />
    </div>
  );
}
