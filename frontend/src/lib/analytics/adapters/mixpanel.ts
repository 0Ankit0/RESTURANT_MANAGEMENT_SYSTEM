import mixpanel from 'mixpanel-browser';
import type { AnalyticsAdapter } from '../interface';

export class MixpanelAdapter implements AnalyticsAdapter {
  constructor(token: string, host?: string) {
    mixpanel.init(token, {
      api_host: host,
      track_pageview: false,
      persistence: 'localStorage',
    });
  }

  capture(event: string, properties?: Record<string, unknown>): void {
    mixpanel.track(event, properties);
  }

  identify(userId: string, properties?: Record<string, unknown>): void {
    mixpanel.identify(userId);
    if (properties) {
      mixpanel.people.set(properties);
    }
  }

  reset(): void {
    mixpanel.reset();
  }

  page(name?: string, properties?: Record<string, unknown>): void {
    mixpanel.track('page_view', { page: name, url: window.location.href, ...properties });
  }

  group(groupType: string, groupKey: string, properties?: Record<string, unknown>): void {
    mixpanel.set_group(groupType, groupKey);
    if (properties) {
      mixpanel.get_group(groupType, groupKey).set(properties);
    }
  }

  getFeatureFlag(): boolean | string | undefined {
    return undefined;
  }

  isFeatureFlagEnabled(): boolean {
    return false;
  }

  reloadFeatureFlags(): void {}
}
