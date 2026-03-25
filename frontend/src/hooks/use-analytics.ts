'use client';

import { analytics } from '@/lib/analytics';

/**
 * React hook that returns the analytics service singleton.
 *
 * Usage:
 *   const { capture, identify, isEnabled } = useAnalytics();
 *   capture('button_clicked', { label: 'Sign up' });
 */
export function useAnalytics() {
  return {
    /** True when analytics are configured and enabled. */
    isEnabled: analytics.enabled,

    /** Record a named event with optional properties. */
    capture: analytics.capture.bind(analytics),

    /** Attach persistent traits to the current user. */
    identify: analytics.identify.bind(analytics),

    /** Disassociate the current user (call on logout). */
    reset: analytics.reset.bind(analytics),

    /** Record a page view. */
    page: analytics.page.bind(analytics),

    /** Associate the current user with a group / tenant. */
    group: analytics.group.bind(analytics),

    /** Get a feature flag value. */
    getFeatureFlag: analytics.getFeatureFlag.bind(analytics),

    /** True when the feature flag is enabled. */
    isFeatureFlagEnabled: analytics.isFeatureFlagEnabled.bind(analytics),

    /** Force-reload feature flags from the server. */
    reloadFeatureFlags: analytics.reloadFeatureFlags.bind(analytics),
  };
}
