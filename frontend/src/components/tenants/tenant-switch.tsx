'use client';

import { useState } from 'react';
import { useTenants, useSwitchTenant } from '@/hooks/use-tenants';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import { Building2, Check, ChevronDown, Plus } from 'lucide-react';
import type { Tenant } from '@/types';

interface TenantSwitchProps {
  onCreateNew?: () => void;
}

export function TenantSwitch({ onCreateNew }: TenantSwitchProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data, isLoading } = useTenants();
  const switchTenant = useSwitchTenant();
  const { tenant: currentTenant } = useAuthStore();

  const tenants = data?.items || [];

  const handleSelect = (tenant: Tenant) => {
    switchTenant.mutate(tenant);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 min-w-[200px] justify-between"
      >
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4" />
          <span className="truncate">{currentTenant?.name || 'Select Organization'}</span>
        </div>
        <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 mt-2 w-full min-w-[240px] bg-white border border-gray-200 rounded-lg shadow-lg z-20">
            {isLoading ? (
              <div className="p-4">
                <div className="animate-pulse space-y-2">
                  <div className="h-4 bg-gray-200 rounded" />
                  <div className="h-4 bg-gray-200 rounded" />
                </div>
              </div>
            ) : (
              <>
                <div className="p-2 max-h-60 overflow-y-auto">
                  {tenants.map((tenant) => (
                    <button
                      key={tenant.id}
                      onClick={() => handleSelect(tenant)}
                      className="w-full flex items-center justify-between p-2 rounded hover:bg-gray-100 text-left"
                    >
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-gray-400" />
                        <span className="text-sm font-medium">{tenant.name}</span>
                      </div>
                      {currentTenant?.id === tenant.id && (
                        <Check className="h-4 w-4 text-blue-600" />
                      )}
                    </button>
                  ))}
                </div>
                {onCreateNew && (
                  <div className="border-t border-gray-200 p-2">
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        onCreateNew();
                      }}
                      className="w-full flex items-center gap-2 p-2 rounded hover:bg-gray-100 text-left text-blue-600"
                    >
                      <Plus className="h-4 w-4" />
                      <span className="text-sm font-medium">Create Organization</span>
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
