'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Radar,
  ShieldAlert,
  Users,
  Shield,
  ArrowLeft,
} from 'lucide-react';
import { OrgSwitcher } from './org-switcher';

const adminNavigation = [
  { name: 'Admin Dashboard', href: '/admin/dashboard', icon: LayoutDashboard },
  { name: 'Logs', href: '/admin/logs', icon: Radar },
  { name: 'Security Review', href: '/admin/security-review', icon: ShieldAlert },
  { name: 'Manage Users', href: '/admin/users', icon: Users },
  { name: 'Roles & Permissions', href: '/admin/rbac', icon: Shield },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-10 w-64 bg-white border-r border-gray-200">
      <div className="flex h-16 items-center justify-center border-b border-gray-200">
        <Link href="/admin/dashboard" className="text-xl font-bold text-blue-600">
          Admin Panel
        </Link>
      </div>
      <OrgSwitcher />
      <nav className="flex flex-col gap-1 p-4 pt-0">
        <div className="mb-2 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">
          Administration
        </div>
        {adminNavigation.map((item) => {
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
        <div className="mt-4 pt-4 border-t border-gray-200">
          <Link
            href="/dashboard"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
            Back to Workspace
          </Link>
        </div>
      </nav>
    </aside>
  );
}
