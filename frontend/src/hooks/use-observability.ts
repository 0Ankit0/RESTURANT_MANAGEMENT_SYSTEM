'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/lib/api-client';
import type {
  ObservabilityLogEntry,
  ObservabilityLogSummary,
  PaginatedResponse,
  SecurityIncident,
  SecurityIncidentStatusUpdate,
} from '@/types';

export interface ObservabilityLogFilters {
  skip?: number;
  limit?: number;
  level?: string;
  source?: string;
  search?: string;
  event_code?: string;
  route?: string;
  user_id?: string;
  request_id?: string;
  log_id?: string;
}

export interface SecurityIncidentFilters {
  skip?: number;
  limit?: number;
  status?: string;
  severity?: string;
  signal_type?: string;
  search?: string;
}

export function useObservabilityLogs(filters: ObservabilityLogFilters) {
  return useQuery({
    queryKey: ['observability-logs', filters],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<ObservabilityLogEntry>>('/observability/logs', {
        params: filters,
      });
      return response.data;
    },
    staleTime: 10_000,
  });
}

export function useLiveObservabilityLogs(
  afterId: string | null,
  enabled: boolean,
  filters?: Pick<ObservabilityLogFilters, 'source' | 'level'>
) {
  return useQuery({
    queryKey: ['observability-live-logs', afterId, filters],
    queryFn: async () => {
      const response = await apiClient.get<ObservabilityLogEntry[]>('/observability/logs/live', {
        params: {
          after_id: afterId ?? undefined,
          ...filters,
        },
      });
      return response.data;
    },
    enabled,
    refetchInterval: enabled ? 2_000 : false,
    refetchIntervalInBackground: true,
  });
}

export function useObservabilitySummary() {
  return useQuery({
    queryKey: ['observability-summary'],
    queryFn: async () => {
      const response = await apiClient.get<ObservabilityLogSummary>('/observability/logs/summary');
      return response.data;
    },
    staleTime: 15_000,
    refetchInterval: 15_000,
  });
}

export function useSecurityIncidents(filters: SecurityIncidentFilters) {
  return useQuery({
    queryKey: ['security-incidents', filters],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<SecurityIncident>>('/observability/incidents', {
        params: filters,
      });
      return response.data;
    },
    staleTime: 10_000,
  });
}

export function useSecurityIncident(incidentId: string | null) {
  return useQuery({
    queryKey: ['security-incident', incidentId],
    queryFn: async () => {
      const response = await apiClient.get<SecurityIncident>(`/observability/incidents/${incidentId}`);
      return response.data;
    },
    enabled: Boolean(incidentId),
  });
}

export function useUpdateSecurityIncident() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ incidentId, payload }: { incidentId: string; payload: SecurityIncidentStatusUpdate }) => {
      const response = await apiClient.patch<SecurityIncident>(`/observability/incidents/${incidentId}`, payload);
      return response.data;
    },
    onSuccess: (incident) => {
      queryClient.invalidateQueries({ queryKey: ['security-incidents'] });
      queryClient.setQueryData(['security-incident', incident.id], incident);
      queryClient.invalidateQueries({ queryKey: ['observability-summary'] });
    },
  });
}
