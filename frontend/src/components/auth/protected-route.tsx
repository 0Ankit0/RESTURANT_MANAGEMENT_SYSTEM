'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import axios from 'axios';
import { useAuthStore } from '@/store/auth-store';
import { apiClient } from '@/lib/api-client';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isAuthenticated, _hasHydrated, setUser, setTokens, logout } = useAuthStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    if (!_hasHydrated) return;

    async function initAuth() {
      // Already authenticated — fetch current user to keep store fresh
      if (isAuthenticated) {
        try {
          const res = await apiClient.get('/users/me');
          setUser(res.data);
        } catch {
          // access token invalid — fall through to refresh attempt below
          // (api-client interceptor already handles 401 refresh, but we catch here too)
        }
        setIsInitializing(false);
        return;
      }

      // Not authenticated — check if a refresh token is stored
      const refreshToken =
        typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;

      if (!refreshToken) {
        // No refresh token at all → go to login
        router.push('/login');
        setIsInitializing(false);
        return;
      }

      // Try to exchange the refresh token for a new token pair
      try {
        const refreshRes = await axios.post(
          `${baseURL}/auth/refresh/`,
          { refresh_token: refreshToken },
          { params: { set_cookie: false } }
        );
        const { access, refresh } = refreshRes.data;
        setTokens(access, refresh);

        // Fetch user with the new access token
        const userRes = await apiClient.get('/users/me', {
          headers: { Authorization: `Bearer ${access}` },
        });
        setUser(userRes.data);
      } catch {
        // Refresh failed (token expired / revoked) → clear everything and go to login
        logout();
        router.push('/login');
      } finally {
        setIsInitializing(false);
      }
    }

    initAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [_hasHydrated]);

  // While Zustand is rehydrating from localStorage or we're attempting a refresh
  if (!_hasHydrated || isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  // Refresh failed and router.push('/login') is in-flight — show spinner
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return <>{children}</>;
}
