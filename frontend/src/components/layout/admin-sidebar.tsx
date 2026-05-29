'use client';

import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Radar,
  ShieldAlert,
  Users,
  Shield,
  ArrowLeft,
} from 'lucide-react';
import { OrgSwitcher } from './org-switcher';
import { useI18n } from '@/lib/i18n';

const adminNavigation = [
  { key: 'admin.adminDashboard', href: '/admin/dashboard', icon: LayoutDashboard },
  { key: 'admin.logs', href: '/admin/logs', icon: Radar },
  { key: 'admin.securityReview', href: '/admin/security-review', icon: ShieldAlert },
  { key: 'admin.manageUsers', href: '/admin/users', icon: Users },
  { key: 'admin.rolesPermissions', href: '/admin/rbac', icon: Shield },
];

export function AdminSidebar() {
  const { t } = useI18n();
  const pathname = useLocation().pathname;

  return (
    <aside className="fixed inset-y-0 left-0 z-10 w-64 bg-white border-r border-gray-200">
      <div className="flex h-16 items-center justify-center border-b border-gray-200">
        <Link to="/admin/dashboard" className="text-xl font-bold text-blue-600">
          {t('admin.panel')}
        </Link>
      </div>
      <OrgSwitcher />
      <nav className="flex flex-col gap-1 p-4 pt-0">
        <div className="mb-2 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">
          {t('admin.administration')}
        </div>
        {adminNavigation.map((item) => {
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
        <div className="mt-4 pt-4 border-t border-gray-200">
          <Link
            to="/dashboard"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
            {t('admin.backToWorkspace')}
          </Link>
        </div>
      </nav>
    </aside>
  );
}
