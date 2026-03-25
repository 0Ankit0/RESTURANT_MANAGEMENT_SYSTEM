/**
 * PostHog analytics adapter.
 *
 * Adapts the posthog-js browser SDK to the AnalyticsAdapter interface.
 * Only instantiated client-side when NEXT_PUBLIC_ANALYTICS_ENABLED=true
 * and NEXT_PUBLIC_POSTHOG_KEY is set.
 *
 * To add a new provider (e.g. Mixpanel):
 *   1. Create adapters/mixpanel.ts implementing AnalyticsAdapter.
 *   2. Register it in ../service.ts factory logic.
 */
import posthog from 'posthog-js';
import type { AnalyticsAdapter } from '../interface';

export class PostHogAdapter implements AnalyticsAdapter {
  constructor(apiKey: string, host: string) {
    posthog.init(apiKey, {
      api_host: host,
      // Respect user privacy — disable automatic pageview capture;
      // we call page() explicitly from the Next.js router.
      capture_pageview: false,
      // Persist identity across sessions
      persistence: 'localStorage',
    });
  }

  capture(event: string, properties?: Record<string, unknown>): void {
    posthog.capture(event, properties);
  }

  identify(userId: string, properties?: Record<string, unknown>): void {
    posthog.identify(userId, properties);
  }

  reset(): void {
    posthog.reset();
  }

  page(name?: string, properties?: Record<string, unknown>): void {
    posthog.capture('$pageview', { $current_url: window.location.href, page: name, ...properties });
  }

  group(groupType: string, groupKey: string, properties?: Record<string, unknown>): void {
    posthog.group(groupType, groupKey, properties);
  }

  getFeatureFlag(flag: string): boolean | string | undefined {
    return posthog.getFeatureFlag(flag) as boolean | string | undefined;
  }

  isFeatureFlagEnabled(flag: string): boolean {
    return posthog.isFeatureEnabled(flag) ?? false;
  }

  reloadFeatureFlags(): void {
    posthog.reloadFeatureFlags();
  }
}
