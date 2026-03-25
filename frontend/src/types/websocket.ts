// WebSocket module types

export interface WebSocketMessage {
  type: string;
  data: unknown;
}

export interface WebSocketStats {
  total_connections: number;
  rooms: Record<string, number>;
  users_online: string[];
}
