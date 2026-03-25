'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { TokenTracking, PaginatedResponse } from '@/types';

export function useTokens(params?: { skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ['tokens', params],
    queryFn: async () => {
      const response = await apiClient.get<PaginatedResponse<TokenTracking>>('/tokens/', {
        params,
      });
      return response.data;
    },
  });
}

export function useRevokeToken() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (tokenId: string) => {
      const response = await apiClient.post(`/tokens/revoke/${tokenId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] });
    },
  });
}

export function useRevokeAllTokens() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/tokens/revoke-all');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tokens'] });
    },
  });
}
