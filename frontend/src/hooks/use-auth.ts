'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/store/auth-store';
import { analytics } from '@/lib/analytics';
import { AuthEvents } from '@/lib/analytics/events';
import type {
  LoginCredentials,
  SignupData,
  AuthTokens,
  User,
  OTPLoginResponse,
  VerifyOTPData,
  OTPSetupResponse,
  ChangePasswordData,
  ResetPasswordRequestData,
  ResetPasswordConfirmData,
} from '@/types';

export function useAuth() {
  const queryClient = useQueryClient();
  const { user, setUser, setTokens, logout: storeLogout } = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await apiClient.post<AuthTokens | OTPLoginResponse>(
        '/auth/login/',
        credentials,
        { params: { set_cookie: false } }
      );
      return response.data;
    },
    onSuccess: (data) => {
      if ('requires_otp' in data) return;
      const tokens = data as AuthTokens;
      setTokens(tokens.access, tokens.refresh);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      analytics.capture(AuthEvents.LOGGED_IN, { method: 'email' });
    },
  });

  const signupMutation = useMutation({
    mutationFn: async (data: SignupData) => {
      const response = await apiClient.post<AuthTokens>(
        '/auth/signup/',
        data,
        { params: { set_cookie: false } }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      analytics.capture(AuthEvents.SIGNED_UP);
    },
  });

  const { data: currentUser, refetch: refetchUser } = useQuery({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const response = await apiClient.get<User>('/users/me/');
      const u = response.data;
      setUser(u);
      analytics.identify(String(u.id), { email: u.email, username: u.username });
      return u;
    },
    enabled: typeof window !== 'undefined' && !!localStorage.getItem('access_token'),
  });

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout/');
    } catch {
      // ignore logout errors
    } finally {
      analytics.capture(AuthEvents.LOGGED_OUT);
      analytics.reset();
      storeLogout();
      queryClient.clear();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  };

  return {
    user: currentUser || user,
    isAuthenticated: !!(currentUser || user),
    login: loginMutation.mutate,
    loginAsync: loginMutation.mutateAsync,
    signup: signupMutation.mutate,
    signupAsync: signupMutation.mutateAsync,
    logout,
    refetchUser,
    isLoading: loginMutation.isPending || signupMutation.isPending,
    loginError: loginMutation.error,
    signupError: signupMutation.error,
  };
}

export function useVerifyOTP() {
  const { setTokens } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: VerifyOTPData) => {
      const response = await apiClient.post<AuthTokens>(
        '/auth/otp/validate/',
        data,
        { params: { set_cookie: false } }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      analytics.capture(AuthEvents.LOGGED_IN, { method: 'otp' });
    },
  });
}

export function useEnableOTP() {
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<OTPSetupResponse>('/auth/otp/enable/');
      return response.data;
    },
  });
}

export function useConfirmOTP() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (otp_code: string) => {
      const response = await apiClient.post('/auth/otp/verify/', { otp_code, temp_token: '' });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      analytics.capture(AuthEvents.OTP_ENABLED);
    },
  });
}

export function useDisableOTP() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (password: string) => {
      const response = await apiClient.post('/auth/otp/disable/', { password });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      analytics.capture(AuthEvents.OTP_DISABLED);
    },
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: async (data: ResetPasswordRequestData) => {
      const response = await apiClient.post('/auth/password-reset-request/', data);
      return response.data;
    },
    onSuccess: () => {
      analytics.capture(AuthEvents.PASSWORD_RESET_REQUESTED);
    },
  });
}

export function useConfirmPasswordReset() {
  return useMutation({
    mutationFn: async (data: ResetPasswordConfirmData) => {
      const response = await apiClient.post('/auth/password-reset-confirm/', data);
      return response.data;
    },
    onSuccess: () => {
      analytics.capture(AuthEvents.PASSWORD_RESET_COMPLETED);
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: ChangePasswordData) => {
      const response = await apiClient.post('/auth/change-password/', data);
      return response.data;
    },
    onSuccess: () => {
      analytics.capture(AuthEvents.PASSWORD_CHANGED);
    },
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: async (t: string) => {
      const response = await apiClient.post('/auth/verify-email/', null, { params: { t } });
      return response.data;
    },
    onSuccess: () => {
      analytics.capture(AuthEvents.EMAIL_VERIFIED);
    },
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/auth/resend-verification/');
      return response.data;
    },
  });
}

