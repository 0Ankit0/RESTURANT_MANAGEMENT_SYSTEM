'use client';

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { apiClient } from '@/lib/api-client';
import type {
  CapabilitySummary,
  MapConfigResponse,
  ProviderStatusResponse,
  PushConfigResponse,
} from '@/types';

export function useSystemCapabilities() {
  return useQuery({
    queryKey: ['system-capabilities'],
    queryFn: async () => {
      const response = await apiClient.get<CapabilitySummary>('/system/capabilities/');
      return response.data;
    },
    staleTime: 60_000,
  });
}

export function useSystemProviders() {
  return useQuery({
    queryKey: ['system-providers'],
    queryFn: async () => {
      const response = await apiClient.get<ProviderStatusResponse>('/system/providers/');
      return response.data;
    },
    staleTime: 60_000,
  });
}

export function usePushConfig() {
  return useQuery({
    queryKey: ['push-config'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<PushConfigResponse>('/notifications/push/config/');
        return response.data;
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 503) {
          return {
            provider: null,
            providers: {
              webpush: { enabled: false },
              fcm: { enabled: false },
              onesignal: { enabled: false },
            },
          } satisfies PushConfigResponse;
        }
        throw error;
      }
    },
    staleTime: 60_000,
  });
}

export function useMapConfig() {
  return useQuery({
    queryKey: ['maps-config'],
    queryFn: async () => {
      const response = await apiClient.get<MapConfigResponse>('/system/maps/config/');
      return response.data;
    },
    staleTime: 60_000,
  });
}
