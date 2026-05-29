'use client';

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ProtectedRoute } from './protected-route';
import { useAuthStore } from '@/store/auth-store';

export function SuperuserRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (user && !user.is_superuser) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  if (user && !user.is_superuser) return null;

  return <ProtectedRoute>{children}</ProtectedRoute>;
}
