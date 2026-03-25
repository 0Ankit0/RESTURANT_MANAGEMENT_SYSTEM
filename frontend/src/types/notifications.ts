// Notification module types

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  body: string;
  type: NotificationType;
  is_read: boolean;
  extra_data?: unknown;
  created_at: string;
}

export interface NotificationList {
  items: Notification[];
  total: number;
  unread_count: number;
}

export interface NotificationPreference {
  id: string;
  user_id: string;
  websocket_enabled: boolean;
  email_enabled: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
  push_endpoint?: string;
  push_provider?: string | null;
  push_providers: string[];
}

export interface NotificationPreferenceUpdate {
  websocket_enabled?: boolean;
  email_enabled?: boolean;
  push_enabled?: boolean;
  sms_enabled?: boolean;
}

export type NotificationDeviceProvider = 'webpush' | 'fcm' | 'onesignal';
export type NotificationDevicePlatform = 'web' | 'android' | 'ios';

export interface NotificationDevice {
  id: string;
  provider: NotificationDeviceProvider;
  platform: NotificationDevicePlatform;
  token?: string | null;
  endpoint?: string | null;
  subscription_id?: string | null;
  is_active: boolean;
  last_seen_at: string;
  created_at: string;
}

export interface NotificationDeviceCreate {
  provider: NotificationDeviceProvider;
  platform: NotificationDevicePlatform;
  token?: string;
  endpoint?: string;
  p256dh?: string;
  auth?: string;
  subscription_id?: string;
  device_metadata?: Record<string, unknown>;
}
