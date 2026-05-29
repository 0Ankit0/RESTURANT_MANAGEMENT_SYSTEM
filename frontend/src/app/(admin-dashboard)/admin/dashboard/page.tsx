'use client';

import { Link } from 'react-router-dom';
import { useAuthStore } from '@/store/auth-store';
import { useListUsers } from '@/hooks/use-users';
import { useTokens } from '@/hooks/use-tokens';
import { useRoles } from '@/hooks/use-rbac';
import { useObservabilitySummary } from '@/hooks/use-observability';
import { useDayCloseBlockers, useLatestOpenDayClose, useRestaurantBranches } from '@/hooks/use-restaurant';
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
import { useI18n } from '@/lib/i18n';

export default function AdminDashboardPage() {
  const { t } = useI18n();
  const user = useAuthStore((state) => state.user);
  const { data: usersData } = useListUsers({ limit: 100 });
  const { data: tokenData } = useTokens({ limit: 1 });
  const { data: rolesData } = useRoles();
  const { data: observabilitySummary } = useObservabilitySummary();
  const { data: branches = [] } = useRestaurantBranches();
  const primaryBranchId = branches[0]?.id ?? 0;
  const latestDayClose = useLatestOpenDayClose(primaryBranchId);
  const blockers = useDayCloseBlockers(latestDayClose.data?.id ?? null);

  const users = usersData?.items ?? [];
  const totalUsers = usersData?.total ?? users.length;
  const activeUsers = users.filter((member) => member.is_active).length;
  const superusers = users.filter((member) => member.is_superuser).length;
  const unverifiedUsers = users.filter((member) => !member.is_confirmed).length;
  const activeSessions = tokenData?.total ?? 0;
  const totalRoles = rolesData?.total ?? rolesData?.items.length ?? 0;

  const stats = [
    {
      name: t('adminDashboard.totalUsers'),
      value: String(totalUsers),
      icon: Users,
      href: '/admin/users',
      color: 'text-blue-600 bg-blue-50',
    },
    {
      name: t('dashboard.activeSessions'),
      value: String(activeSessions),
      icon: Key,
      href: '/tokens',
      color: 'text-purple-600 bg-purple-50',
    },
    {
      name: t('adminDashboard.rolesPermissions'),
      value: String(totalRoles),
      icon: Shield,
      href: '/admin/rbac',
      color: 'text-green-600 bg-green-50',
    },
    {
      name: t('adminDashboard.superusers'),
      value: String(superusers),
      icon: UserCheck,
      href: '/admin/users',
      color: 'text-amber-600 bg-amber-50',
    },
    {
      name: t('adminDashboard.openIncidents'),
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
      label: t('adminDashboard.manageUsers'),
      desc: t('adminDashboard.reviewAccounts'),
      color: 'text-blue-600',
    },
    {
      href: '/admin/rbac',
      icon: Shield,
      label: t('adminDashboard.rolesPermissions'),
      desc: t('adminDashboard.tuneRoles'),
      color: 'text-green-600',
    },
    {
      href: '/admin/logs',
      icon: Activity,
      label: t('adminDashboard.liveLogs'),
      desc: t('adminDashboard.watchEvents'),
      color: 'text-blue-600',
    },
    {
      href: '/admin/security-review',
      icon: ShieldAlert,
      label: t('adminDashboard.securityReview'),
      desc: t('adminDashboard.triageActivity'),
      color: 'text-red-600',
    },
    {
      href: '/tokens',
      icon: Key,
      label: t('dashboard.activeSessions'),
      desc: t('adminDashboard.monitorTokens'),
      color: 'text-purple-600',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('adminDashboard.title')}</h1>
        <p className="text-gray-500">
          {t('dashboard.welcomeBack', {
            name: user?.first_name || user?.username || t('header.user'),
          })}
          {' '}
          {t('adminDashboard.overview')}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link key={stat.name} to={stat.href}>
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
              {t('dashboard.quickActions')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((item) => (
                <Link
                  key={item.href}
                  to={item.href}
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
              {t('adminDashboard.userOverview')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link
              to="/admin/users"
              className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-blue-400 hover:bg-blue-50"
            >
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="text-sm text-gray-900">{t('adminDashboard.activeUsers')}</span>
              </div>
              <span className="text-xs text-gray-500">{t('adminDashboard.accounts', { count: activeUsers })}</span>
            </Link>
            <Link
              to="/admin/users"
              className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-blue-400 hover:bg-blue-50"
            >
              <div className="flex items-center gap-3">
                <UserCheck className="h-5 w-5 text-amber-600" />
                <span className="text-sm text-gray-900">{t('adminDashboard.superuserAccess')}</span>
              </div>
              <span className="text-xs text-gray-500">{t('adminDashboard.elevatedUsers', { count: superusers })}</span>
            </Link>
            <Link
              to="/admin/users"
              className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:border-blue-400 hover:bg-blue-50"
            >
              <div className="flex items-center gap-3">
                <UserX className="h-5 w-5 text-red-600" />
                <span className="text-sm text-gray-900">{t('adminDashboard.unverifiedAccounts')}</span>
              </div>
              <span className="text-xs text-gray-500">{t('adminDashboard.pendingReview', { count: unverifiedUsers })}</span>
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
                <p className="text-sm font-medium text-yellow-800">{t('adminDashboard.accountsNeedAttention')}</p>
                <p className="mt-1 text-xs text-yellow-700">
                  {t('adminDashboard.needVerification', {
                    count: unverifiedUsers,
                    suffix: unverifiedUsers === 1 ? '' : 's',
                  })}
                </p>
              </div>
              <Link
                to="/admin/users"
                className="flex-shrink-0 text-sm font-medium text-yellow-700 underline hover:text-yellow-900"
              >
                {t('adminDashboard.reviewUsers')}
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>{t('adminDashboard.operationsBlockers')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {!latestDayClose.data && <p className="text-gray-500">{t('adminDashboard.noActiveDayClose')}</p>}
          {blockers.data?.blockers?.map((blocker) => (
            <div key={blocker.blocker_code} className="rounded border p-2">
              <p className="font-medium">{blocker.summary}</p>
              <p className="text-xs text-gray-500">
                {t('adminDashboard.severityCount', {
                  severity: blocker.severity,
                  count: blocker.count,
                })}
              </p>
            </div>
          ))}
          {latestDayClose.data && !blockers.data?.blockers?.length && (
            <p className="text-emerald-700">{t('adminDashboard.noBlockers')}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
