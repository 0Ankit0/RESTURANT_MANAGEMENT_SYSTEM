'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
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
} from 'lucide-react';
import { OrgSwitcher } from './org-switcher';
import { useSystemCapabilities } from '@/hooks/use-system';
import { useAuthStore } from '@/store/auth-store';

const mainNavigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Profile', href: '/profile', icon: User },
  { name: 'Tenants', href: '/tenants', icon: Building2, feature: 'multitenancy' },
  { name: 'Payments', href: '/finances', icon: CreditCard, feature: 'finance' },
  { name: 'Notifications', href: '/notifications', icon: Bell, feature: 'notifications' },
  { name: 'Maps', href: '/maps', icon: Map, feature: 'maps' },
  { name: 'Active Sessions', href: '/tokens', icon: Key, feature: 'auth' },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
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
        <Link href="/dashboard" className="text-xl font-bold text-blue-600">
          {appName}
        </Link>
      </div>
      <OrgSwitcher />
      <nav className="flex flex-col gap-1 p-4 pt-0">
        <div className="mb-2 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">
          Workspace
        </div>
        {visibleNavigation.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
        {showAdminSwitch ? (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <Link
              href="/admin/dashboard"
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
            >
              <ArrowRight className="h-5 w-5" />
              Open Admin Panel
            </Link>
          </div>
        ) : null}
      </nav>
    </aside>
  );
}
