export interface CapabilitySummary {
  modules: Record<string, boolean>;
  active_providers: Record<string, string | null>;
  fallback_providers: Record<string, string[]>;
}

export interface ProviderStatus {
  channel: string;
  provider: string;
  active: boolean;
  enabled: boolean;
  configured: boolean;
  fallback: boolean;
}

export interface ProviderStatusResponse {
  providers: ProviderStatus[];
}

export interface PushProviderConfig {
  enabled: boolean;
  vapid_public_key?: string;
  project_id?: string;
  web_vapid_key?: string;
  api_key?: string;
  app_id?: string;
  messaging_sender_id?: string;
  auth_domain?: string;
  storage_bucket?: string;
  measurement_id?: string;
  web_app_id?: string;
}

export interface PushConfigResponse {
  provider: string | null;
  providers: {
    webpush: PushProviderConfig;
    fcm: PushProviderConfig;
    onesignal: PushProviderConfig;
  };
}

export interface MapProviderConfig {
  enabled: boolean;
  label: string;
  api_key?: string;
  map_id?: string;
}

export interface MapConfigResponse {
  enabled: boolean;
  provider: 'osm' | 'google' | null;
  default_center: {
    latitude: number;
    longitude: number;
    zoom: number;
  };
  providers: {
    osm: MapProviderConfig;
    google: MapProviderConfig;
  };
}
