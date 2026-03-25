'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from './protected-route';
import { useAuthStore } from '@/store/auth-store';

export function SuperuserRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (user && !user.is_superuser) {
      router.replace('/dashboard');
    }
  }, [user, router]);

  if (user && !user.is_superuser) return null;

  return <ProtectedRoute>{children}</ProtectedRoute>;
}
