'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { ChevronsUpDown, Check, Building2, Plus } from 'lucide-react';
import { useAuthStore } from '@/store/auth-store';
import { useTenants, useSwitchTenant } from '@/hooks/use-tenants';
import type { Tenant } from '@/types';

function OrgAvatar({ name, className = '' }: { name: string; className?: string }) {
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');
  // Deterministic colour from name
  const colours = [
    'bg-blue-500', 'bg-violet-500', 'bg-emerald-500',
    'bg-orange-500', 'bg-pink-500', 'bg-cyan-500',
  ];
  const colour = colours[name.charCodeAt(0) % colours.length];
  return (
    <span
      className={`inline-flex items-center justify-center rounded-md text-white font-semibold text-xs ${colour} ${className}`}
    >
      {initials || <Building2 className="h-3 w-3" />}
    </span>
  );
}

export function OrgSwitcher() {
  const { tenant: activeTenant, setTenant } = useAuthStore();
  const { data } = useTenants({ limit: 50 });
  const switchTenant = useSwitchTenant();

  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const tenants: Tenant[] = data?.items ?? [];

  const handleSwitch = (t: Tenant) => {
    switchTenant.mutate(t);
    setOpen(false);
  };

  const handlePersonal = () => {
    setTenant(null);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative px-3 pb-3 pt-1">
      {/* Trigger */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {activeTenant ? (
          <OrgAvatar name={activeTenant.name} className="h-6 w-6 flex-shrink-0" />
        ) : (
          <span className="inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md bg-gray-200">
            <Building2 className="h-3.5 w-3.5 text-gray-500" />
          </span>
        )}
        <span className="flex-1 truncate text-left">
          {activeTenant ? activeTenant.name : 'Personal'}
        </span>
        <ChevronsUpDown className="h-3.5 w-3.5 text-gray-400 flex-shrink-0" />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute left-3 right-3 top-full mt-1 z-50 rounded-xl border border-gray-200 bg-white shadow-lg overflow-hidden">
          {/* Section: personal */}
          <div className="px-2 py-1.5">
            <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
              Account
            </p>
            <button
              onClick={handlePersonal}
              className="flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <span className="inline-flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md bg-gray-200">
                <Building2 className="h-3.5 w-3.5 text-gray-500" />
              </span>
              <span className="flex-1 truncate text-left">Personal</span>
              {!activeTenant && <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />}
            </button>
          </div>

          {/* Section: organizations */}
          {tenants.length > 0 && (
            <div className="border-t border-gray-100 px-2 py-1.5">
              <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                Organizations
              </p>
              <ul className="max-h-48 overflow-y-auto" role="listbox">
                {tenants.map((t) => {
                  const isActive = activeTenant?.id === t.id;
                  return (
                    <li key={t.id} role="option" aria-selected={isActive}>
                      <button
                        onClick={() => handleSwitch(t)}
                        className="flex w-full items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        <OrgAvatar name={t.name} className="h-6 w-6 flex-shrink-0" />
                        <span className="flex-1 truncate text-left">{t.name}</span>
                        {isActive && <Check className="h-4 w-4 text-blue-600 flex-shrink-0" />}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Footer: create new org */}
          <div className="border-t border-gray-100">
            <Link
              href="/tenants"
              onClick={() => setOpen(false)}
              className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <Plus className="h-4 w-4 text-gray-400" />
              Add organization
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
