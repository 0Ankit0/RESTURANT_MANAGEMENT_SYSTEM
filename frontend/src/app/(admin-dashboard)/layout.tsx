'use client';

import { SuperuserRoute } from '@/components/auth/superuser-route';
import { AdminSidebar } from '@/components/layout/admin-sidebar';
import { Header } from '@/components/layout/header';

export default function AdminDashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SuperuserRoute>
      <div className="min-h-screen bg-gray-50">
        <AdminSidebar />
        <Header />
        <main className="ml-64 pt-16 p-6">{children}</main>
      </div>
    </SuperuserRoute>
  );
}
