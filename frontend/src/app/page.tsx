'use client';

import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import {
  ChefHat,
  ClipboardCheck,
  CreditCard,
  LayoutDashboard,
  Store,
  Users,
} from 'lucide-react';

const features = [
  {
    icon: LayoutDashboard,
    title: 'Service Dashboard',
    description: 'Track covers, table turns, kitchen load, and unresolved tickets in one live board.',
  },
  {
    icon: Store,
    title: 'Branch Operations',
    description: 'Run reservations, seating, waiter workflows, and cashier settlement per branch.',
  },
  {
    icon: ChefHat,
    title: 'Kitchen Flow',
    description: 'Prioritize prep queues, identify bottlenecks, and close service windows faster.',
  },
  {
    icon: Users,
    title: 'Role-Based Access',
    description: 'Give managers, hosts, floor staff, and admins the exact tools they need.',
  },
  {
    icon: CreditCard,
    title: 'Payments & Settlements',
    description: 'Capture transactions, reconcile payouts, and monitor failed exports in real time.',
  },
  {
    icon: ClipboardCheck,
    title: 'Audit-Ready Activity',
    description: 'Token tracking, security review, and operational logs built into daily workflows.',
  },
];

export default function Home() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_20%_0%,#fff2d9_0%,#fff7eb_35%,#fff_75%)] text-stone-900">
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-amber-200/70 bg-white/85 backdrop-blur-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2 text-xl font-bold text-amber-700">
              <ChefHat className="h-5 w-5" />
              Restaurant Command Center
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost">Sign in</Button>
              </Link>
              <Link to="/signup">
                <Button className="bg-amber-600 hover:bg-amber-700">Start onboarding</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="pt-16">
        <section className="px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-7xl items-center gap-10 lg:grid-cols-2">
            <div>
              <p className="mb-4 inline-flex rounded-full border border-amber-300 bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-700">
                Built for modern restaurant teams
              </p>
              <h1 className="mb-6 text-4xl font-bold leading-tight sm:text-5xl">
                Run service, staff, and settlements from one restaurant operations platform.
              </h1>
              <p className="mb-8 max-w-2xl text-lg text-stone-600">
                Coordinate front-of-house, kitchen, notifications, and finance with a unified system
                designed for multi-branch restaurant management.
              </p>
              <div className="flex flex-col gap-4 sm:flex-row">
                <Link to="/signup">
                  <Button size="lg" className="w-full bg-amber-600 hover:bg-amber-700 sm:w-auto">
                    Launch your workspace
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="outline" size="lg" className="w-full border-amber-300 text-amber-800 sm:w-auto">
                    Sign in to operations
                  </Button>
                </Link>
              </div>
            </div>
            <div className="rounded-2xl border border-amber-200 bg-white p-6 shadow-xl shadow-amber-100">
              <h2 className="mb-5 text-lg font-semibold">Live operations snapshot</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl bg-amber-50 p-4">
                  <p className="text-sm text-stone-500">Open tables</p>
                  <p className="mt-2 text-3xl font-bold text-amber-700">24</p>
                </div>
                <div className="rounded-xl bg-emerald-50 p-4">
                  <p className="text-sm text-stone-500">Kitchen tickets</p>
                  <p className="mt-2 text-3xl font-bold text-emerald-700">11</p>
                </div>
                <div className="rounded-xl bg-sky-50 p-4">
                  <p className="text-sm text-stone-500">Active sessions</p>
                  <p className="mt-2 text-3xl font-bold text-sky-700">18</p>
                </div>
                <div className="rounded-xl bg-rose-50 p-4">
                  <p className="text-sm text-stone-500">Pending blockers</p>
                  <p className="mt-2 text-3xl font-bold text-rose-700">3</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <h2 className="mb-3 text-center text-3xl font-bold">Purpose-built for restaurant workflows</h2>
            <p className="mx-auto mb-12 max-w-3xl text-center text-stone-600">
              Everything from branch staffing to session security is available from the same operational hub.
            </p>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-xl border border-stone-200 p-6 transition-all hover:-translate-y-1 hover:border-amber-400 hover:shadow-lg"
                >
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-amber-100">
                    <feature.icon className="h-6 w-6 text-amber-700" />
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-stone-900">{feature.title}</h3>
                  <p className="text-stone-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl rounded-2xl border border-amber-200 bg-amber-50 p-10 text-center">
            <h2 className="mb-4 text-3xl font-bold text-stone-900">Open your first service-ready dashboard today</h2>
            <p className="mb-8 text-stone-600">
              Create your account, assign branch roles, and begin managing daily operations in minutes.
            </p>
            <Link to="/signup">
              <Button size="lg" className="bg-amber-600 hover:bg-amber-700">Create restaurant account</Button>
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-amber-200 py-8 px-4">
        <div className="mx-auto max-w-7xl text-center text-sm text-stone-500">
          © {new Date().getFullYear()} Restaurant Command Center. Built for daily service excellence.
        </div>
      </footer>
    </div>
  );
}
