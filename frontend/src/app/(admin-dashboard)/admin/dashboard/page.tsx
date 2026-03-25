'use client';

import Link from 'next/link';
import { useAuthStore } from '@/store/auth-store';
import { useListUsers } from '@/hooks/use-users';
import { useTokens } from '@/hooks/use-tokens';
import { useRoles } from '@/hooks/use-rbac';
import { useObservabilitySummary } from '@/hooks/use-observability';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Key,
  Shield,
  ShieldAlert,
  UserCheck,
  UserX,
  Users,
} from 'lucide-react';

export default function AdminDashboardPage() {
  const user = useAuthStore((state) => state.user);
  const { data: usersData } = useListUsers({ limit: 100 });
  const { data: tokenData } = useTokens({ limit: 1 });
  const { data: rolesData } = useRoles();
  const { data: observabilitySummary } = useObservabilitySummary();

  const users = usersData?.items ?? [];
  const totalUsers = usersData?.total ?? users.length;
  const activeUsers = users.filter((member) => member.is_active).length;
  const superusers = users.filter((member) => member.is_superuser).length;
  const unverifiedUsers = users.filter((member) => !member.is_confirmed).length;
  const activeSessions = tokenData?.total ?? 0;
  const totalRoles = rolesData?.total ?? rolesData?.items.length ?? 0;

  const stats = [
    {
      name: 'Total Users',
      value: String(totalUsers),
      icon: Users,
      href: '/admin/users',
      color: 'text-blue-600 bg-blue-50',
    },
    {
      name: 'Active Sessions',
      value: String(activeSessions),
      icon: Key,
      href: '/tokens',
      color: 'text-purple-600 bg-purple-50',
    },
    {
      name: 'Roles & Permissions',
      value: String(totalRoles),
      icon: Shield,
      href: '/admin/rbac',
      color: 'text-green-600 bg-green-50',
    },
    {
      name: 'Superusers',
      value: String(superusers),
      icon: UserCheck,
      href: '/admin/users',
      color: 'text-amber-600 bg-amber-50',
    },
    {
      name: 'Open Incidents',
      value: String(observabilitySummary?.open_incidents ?? 0),
      icon: ShieldAlert,
      href: '/admin/security-review',
      color: 'text-red-600 bg-red-50',
    },
  ];

  const quickActions = [
    {
      href: '/admin/users',
      icon: Users,
      label: 'Manage Users',
      desc: 'Review accounts and edit access',
      color: 'text-blue-600',
    },
    {
      href: '/admin/rbac',
      icon: Shield,
      label: 'Roles & Permissions',
      desc: 'Tune role and permission rules',
      color: 'text-green-600',
    },
    {
      href: '/admin/logs',
      icon: Activity,
      label: 'Live Logs',
      desc: 'Watch the persisted event stream',
      color: 'text-blue-600',
    },
    {
      href: '/admin/security-review',
      icon: ShieldAlert,
      label: 'Security Review',
      desc: 'Triage suspicious activity',
      color: 'text-red-600',
    },
    {
      href: '/tokens',
      icon: Key,
      label: 'Active Sessions',
      desc: 'Monitor and revoke tokens',
      color: 'text-purple-600',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-500">
          Welcome back
          {user?.first_name ? `, ${user.first_name}` : user?.username ? `, ${user.username}` : ''}!
          {' '}Here&apos;s the current platform overview.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link key={stat.name} href={stat.href}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">{stat.name}</p>
                    <p className="mt-1 text-2xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                  <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${stat.color}`}>
                    <stat.icon className="h-6 w-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex flex-col gap-2 rounded-lg border border-gray-200 p-4 transition-colors hover:border-blue-400 hover:bg-blue-50"
                >
                  <item.icon className={`h-5 w-5 ${item.color}`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{item.label}</p>
                    <p className="text-xs text-gray-500">{item.desc}</p>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              User Overview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              href="/admin/users"
              className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-blue-400 hover:bg-blue-50"
            >
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="text-sm text-gray-900">Active users</span>
              </div>
              <span className="text-xs text-gray-500">{activeUsers} accounts</span>
            </Link>
            <Link
              href="/admin/users"
              className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-blue-400 hover:bg-blue-50"
            >
              <div className="flex items-center gap-3">
                <UserCheck className="h-5 w-5 text-amber-600" />
                <span className="text-sm text-gray-900">Superuser access</span>
              </div>
              <span className="text-xs text-gray-500">{superusers} elevated users</span>
            </Link>
            <Link
              href="/admin/users"
              className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-blue-400 hover:bg-blue-50"
            >
              <div className="flex items-center gap-3">
                <UserX className="h-5 w-5 text-red-600" />
                <span className="text-sm text-gray-900">Unverified accounts</span>
              </div>
              <span className="text-xs text-gray-500">{unverifiedUsers} pending review</span>
            </Link>
          </CardContent>
        </Card>
      </div>

      {unverifiedUsers > 0 ? (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-600" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-800">Accounts need attention</p>
                <p className="mt-1 text-xs text-yellow-700">
                  {unverifiedUsers} user account{unverifiedUsers === 1 ? '' : 's'} still need email verification.
                </p>
              </div>
              <Link
                href="/admin/users"
                className="flex-shrink-0 text-sm font-medium text-yellow-700 underline hover:text-yellow-900"
              >
                Review users
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
