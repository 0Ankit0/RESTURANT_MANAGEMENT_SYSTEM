'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { WebSocketStats } from '@/types';

interface WSBaseMessage {
  type: string;
  [key: string]: unknown;
}

interface WSEventMetadataMessage extends WSBaseMessage {
  event_id?: string;
  occurred_at?: string;
  attempt?: number;
}

interface WSEncryptedFrame {
  type: string;
  iv: string;
  data: string;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WSBaseMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

function decodeBase64(value: string): Uint8Array {
  const bin = atob(value);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

async function importAesKey(rawKeyB64: string): Promise<CryptoKey> {
  const keyBytes = decodeBase64(rawKeyB64);
  return crypto.subtle.importKey('raw', keyBytes.buffer as ArrayBuffer, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
}

async function decryptFrame(frame: WSEncryptedFrame, key: CryptoKey): Promise<WSBaseMessage> {
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: decodeBase64(frame.iv).buffer as ArrayBuffer },
    key,
    decodeBase64(frame.data).buffer as ArrayBuffer
  );
  return JSON.parse(new TextDecoder().decode(new Uint8Array(plaintext))) as WSBaseMessage;
}

async function encryptMessage(payload: WSBaseMessage, key: CryptoKey): Promise<WSEncryptedFrame> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(JSON.stringify(payload));
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded);
  return {
    type: payload.type,
    iv: btoa(String.fromCharCode(...iv)),
    data: btoa(String.fromCharCode(...new Uint8Array(ciphertext))),
  };
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
  const sessionKeyRef = useRef<CryptoKey | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (typeof window === 'undefined' || !url) return;

    const token = localStorage.getItem('access_token');
    if (!token) return;

    const ws = new WebSocket(`${url}?token=${token}`);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      onOpen?.();
    };

    ws.onmessage = async (event) => {
      try {
        const incoming = JSON.parse(event.data as string) as WSBaseMessage;
        if (incoming.type === 'handshake' && typeof incoming.session_key === 'string') {
          sessionKeyRef.current = await importAesKey(incoming.session_key);
          return;
        }

        if (typeof incoming.iv === 'string' && typeof incoming.data === 'string' && sessionKeyRef.current) {
          const decrypted = await decryptFrame(incoming as unknown as WSEncryptedFrame, sessionKeyRef.current);
          onMessage?.(decrypted);
          return;
        }

        onMessage?.(incoming);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      sessionKeyRef.current = null;
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
      sessionKeyRef.current = null;
    }
  }, []);

  const send = useCallback(async (data: WSBaseMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (sessionKeyRef.current) {
        const encrypted = await encryptMessage(data, sessionKeyRef.current);
        wsRef.current.send(JSON.stringify(encrypted));
        return;
      }
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
      if (message.type !== 'event') return;
      if (message.event === 'notification.new') {
        queryClient.invalidateQueries({ queryKey: ['notifications'] });
      }
    },
  });
}

/** Connect to a branch room endpoint for restaurant operational real-time refreshes. */
export function useRestaurantOpsWebSocket(branchId: number) {
  const queryClient = useQueryClient();
  const wsBase = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  const seenEventIdsRef = useRef<Set<string>>(new Set());

  return useWebSocket({
    url: branchId > 0 ? `${wsBase}/api/v1/ws/room/branch:${branchId}:ops/` : '',
    onMessage: (message) => {
      if (message.type !== 'event') return;
      const metadata = message as WSEventMetadataMessage;
      if (typeof metadata.event_id === 'string' && metadata.event_id.length > 0) {
        if (seenEventIdsRef.current.has(metadata.event_id)) {
          return;
        }
        seenEventIdsRef.current.add(metadata.event_id);
        if (seenEventIdsRef.current.size > 500) {
          const oldest = seenEventIdsRef.current.values().next().value as string | undefined;
          if (oldest) seenEventIdsRef.current.delete(oldest);
        }
      }
      const event = typeof message.event === 'string' ? message.event : '';
      if (!event.startsWith('restaurant.')) return;

      queryClient.invalidateQueries({ queryKey: ['restaurant', 'branch-report', branchId] });
      queryClient.invalidateQueries({ queryKey: ['restaurant', 'operational-notifications', branchId] });

      if (event.startsWith('restaurant.kitchen.')) {
        queryClient.invalidateQueries({ queryKey: ['restaurant', 'kitchen-tickets'] });
      }
      if (event.startsWith('restaurant.settlement.')) {
        queryClient.invalidateQueries({ queryKey: ['restaurant', 'bills', branchId] });
      }
      if (event.startsWith('restaurant.export.')) {
        queryClient.invalidateQueries({ queryKey: ['restaurant', 'branch-report', branchId] });
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
      if (message.type === 'event') {
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
