'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type {
  NotificationDevice,
  NotificationDeviceCreate,
  NotificationDeviceProvider,
  Notification,
  NotificationList,
  NotificationPreference,
  NotificationPreferenceUpdate,
} from '@/types';

function notificationDeviceEndpoint(provider: NotificationDeviceProvider): string {
  switch (provider) {
    case 'webpush':
      return '/notifications/devices/webpush/';
    case 'fcm':
      return '/notifications/devices/fcm/';
    case 'onesignal':
      return '/notifications/devices/onesignal/';
  }
}

export function useNotifications(params?: { unread_only?: boolean; skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['notifications', params],
    queryFn: async () => {
      const response = await apiClient.get<NotificationList>('/notifications/', { params });
      return response.data;
    },
  });
}

export function useGetNotification(id: string) {
  return useQuery({
    queryKey: ['notifications', id],
    queryFn: async () => {
      const response = await apiClient.get<Notification>(`/notifications/${id}/`);
      return response.data;
    },
    enabled: Boolean(id),
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await apiClient.patch<Notification>(`/notifications/${id}/read/`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.patch('/notifications/read-all/');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/notifications/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

/** Create a notification (superuser only). */
export function useCreateNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      user_id: string;
      title: string;
      body: string;
      type?: string;
    }) => {
      const response = await apiClient.post('/notifications/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

// ── Notification Preferences ────────────────────────────────────────────────

export function useNotificationPreferences(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['notification-preferences'],
    queryFn: async () => {
      const response = await apiClient.get<NotificationPreference>(
        '/notifications/preferences/'
      );
      return response.data;
    },
    enabled: options?.enabled ?? true,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: NotificationPreferenceUpdate) => {
      const response = await apiClient.patch<NotificationPreference>(
        '/notifications/preferences/',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
  });
}

export function useRegisterPushSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { endpoint: string; p256dh: string; auth: string }) => {
      const response = await apiClient.put<NotificationPreference>(
        '/notifications/preferences/push-subscription/',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
  });
}

export function useRemovePushSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.delete('/notifications/preferences/push-subscription/');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
  });
}

export function useNotificationDevices(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['notification-devices'],
    queryFn: async () => {
      const response = await apiClient.get<NotificationDevice[]>('/notifications/devices/');
      return response.data;
    },
    enabled: options?.enabled ?? true,
  });
}

export function useRegisterNotificationDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: NotificationDeviceCreate) => {
      const response = await apiClient.post<NotificationDevice>(
        notificationDeviceEndpoint(data.provider),
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-devices'] });
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
  });
}

export function useRemoveNotificationDevice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/notifications/devices/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-devices'] });
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
  });
}
