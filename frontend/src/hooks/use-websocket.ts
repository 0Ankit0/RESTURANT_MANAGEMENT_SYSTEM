'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { WebSocketStats } from '@/types';

interface WebSocketMessage {
  type: string;
  data: unknown;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onOpen,
  onClose,
  onError,
  reconnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (typeof window === 'undefined' || !url) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    const wsUrl = `${url}?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      onOpen?.();
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data as string) as WebSocketMessage;
        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      onClose?.();
      if (reconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current += 1;
        setTimeout(connect, reconnectInterval);
      }
    };

    ws.onerror = (error) => {
      onError?.(error);
    };

    wsRef.current = ws;
  }, [url, onMessage, onOpen, onClose, onError, reconnect, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((data: unknown) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { isConnected, send, disconnect, reconnect: connect };
}

/** Connect to the global WebSocket endpoint. Invalidates notification queries on incoming events. */
export function useNotificationWebSocket() {
  const queryClient = useQueryClient();
  const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

  return useWebSocket({
    url: `${wsBase}/api/v1/ws/`,
    onMessage: (message) => {
      if (message.type === 'notification' || message.type === 'event') {
        queryClient.invalidateQueries({ queryKey: ['notifications'] });
      }
    },
  });
}

/** Connect to a room WebSocket endpoint (e.g. per-tenant broadcasts). */
export function useTenantWebSocket(tenantId: string | undefined) {
  const queryClient = useQueryClient();
  const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

  return useWebSocket({
    url: tenantId ? `${wsBase}/api/v1/ws/room/${tenantId}/` : '',
    onMessage: (message) => {
      if (message.type === 'tenant_update' || message.type === 'event') {
        queryClient.invalidateQueries({ queryKey: ['tenants', tenantId] });
      }
    },
  });
}

/** Fetch WebSocket connection stats from the REST endpoint. */
export function useWSStats() {
  return useQuery({
    queryKey: ['ws-stats'],
    queryFn: async () => {
      const response = await apiClient.get<WebSocketStats>('/ws/stats/');
      return response.data;
    },
    refetchInterval: 30_000,
  });
}

/** Check if a specific user is online via WebSocket. */
export function useWSIsOnline(userId: string | undefined) {
  return useQuery({
    queryKey: ['ws-online', userId],
    queryFn: async () => {
      const response = await apiClient.get<{ user_id: string; online: boolean }>(
        `/ws/online/${userId}/`
      );
      return response.data;
    },
    enabled: Boolean(userId),
    refetchInterval: 15_000,
  });
}
