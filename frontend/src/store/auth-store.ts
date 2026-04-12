import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Tenant } from '@/types';

interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  isAuthenticated: boolean;
  sessionInvalidated: boolean;
  authMessage: string | null;
  _hasHydrated: boolean;
  setUser: (user: User | null) => void;
  setTokens: (access: string, refresh: string) => void;
  setTenant: (tenant: Tenant | null) => void;
  markSessionInvalidated: (message: string) => void;
  clearAuthMessage: () => void;
  logout: () => void;
  setHasHydrated: (state: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tenant: null,
      isAuthenticated: false,
      sessionInvalidated: false,
      authMessage: null,
      _hasHydrated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user, sessionInvalidated: false }),
      setTokens: (access, refresh) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', access);
          localStorage.setItem('refresh_token', refresh);
        }
      },
      setTenant: (tenant) => {
        set({ tenant });
      },
      markSessionInvalidated: (message) =>
        set({ sessionInvalidated: true, authMessage: message, user: null, isAuthenticated: false }),
      clearAuthMessage: () => set({ authMessage: null }),
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
        set({
          user: null,
          tenant: null,
          isAuthenticated: false,
          sessionInvalidated: false,
          authMessage: null,
        });
      },
      setHasHydrated: (state) => set({ _hasHydrated: state }),
    }),
    {
      name: 'auth-storage',
      // Only persist tokens (stored separately) — never persist user data or
      // isAuthenticated to localStorage. User state must always come from the
      // server, preventing client-side spoofing of roles/permissions.
      partialize: () => ({}),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
