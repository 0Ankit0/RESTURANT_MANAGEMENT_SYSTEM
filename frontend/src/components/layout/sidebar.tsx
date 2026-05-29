'use client';

import { Link, useLocation } from 'react-router-dom';
import {
  Home,
  Bell,
  Settings,
  Building2,
  User,
  CreditCard,
  Key,
  ArrowRight,
  Map,
  UtensilsCrossed,
} from 'lucide-react';
import { OrgSwitcher } from './org-switcher';
import { useSystemCapabilities } from '@/hooks/use-system';
import { useAuthStore } from '@/store/auth-store';
import { useI18n } from '@/lib/i18n';

const mainNavigation = [
  { key: 'sidebar.dashboard', href: '/dashboard', icon: Home },
  { key: 'sidebar.profile', href: '/profile', icon: User },
  { key: 'sidebar.tenants', href: '/tenants', icon: Building2, feature: 'multitenancy' },
  { key: 'sidebar.payments', href: '/finances', icon: CreditCard, feature: 'finance' },
  { key: 'sidebar.notifications', href: '/notifications', icon: Bell, feature: 'notifications' },
  { key: 'sidebar.maps', href: '/maps', icon: Map, feature: 'maps' },
  { key: 'sidebar.restaurantOps', href: '/restaurant', icon: UtensilsCrossed },
  { key: 'sidebar.activeSessions', href: '/tokens', icon: Key, feature: 'auth' },
  { key: 'sidebar.settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const { t } = useI18n();
  const pathname = useLocation().pathname;
  const { data: capabilities } = useSystemCapabilities();
  const user = useAuthStore((state) => state.user);
  const appName = process.env.NEXT_PUBLIC_APP_NAME ?? 'Project Template';

  const visibleNavigation = mainNavigation.filter(
    (item) => !item.feature || capabilities?.modules[item.feature] !== false
  );
  const showAdminSwitch = Boolean(user?.is_superuser);

  return (
    <aside className="fixed inset-y-0 left-0 z-10 w-64 bg-white border-r border-gray-200">
      <div className="flex h-16 items-center justify-center border-b border-gray-200">
        <Link to="/dashboard" className="text-xl font-bold text-blue-600">
          {appName}
        </Link>
      </div>
      <OrgSwitcher />
      <nav className="flex flex-col gap-1 p-4 pt-0">
        <div className="mb-2 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">
          {t('sidebar.workspace')}
        </div>
        {visibleNavigation.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.key}
              to={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <item.icon className="h-5 w-5" />
              {t(item.key)}
            </Link>
          );
        })}
        {showAdminSwitch ? (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <Link
              to="/admin/dashboard"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
            >
              <ArrowRight className="h-5 w-5" />
              {t('sidebar.openAdminPanel')}
            </Link>
          </div>
        ) : null}
      </nav>
    </aside>
  );
}
