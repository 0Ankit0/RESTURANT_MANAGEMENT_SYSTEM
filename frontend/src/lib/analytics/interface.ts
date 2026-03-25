/**
 * Analytics Strategy interface.
 *
 * Every analytics provider (PostHog, Mixpanel, Amplitude, custom…) must
 * implement AnalyticsAdapter.  AnalyticsService depends only on this
 * contract — swapping providers requires only a new adapter class.
 *
 * Pattern notes
 * -------------
 * Strategy  : AnalyticsAdapter defines the operation family.
 *             AnalyticsService uses an adapter instance polymorphically.
 * Adapter   : Concrete adapters (e.g. PostHogAdapter) wrap third-party SDKs
 *             and translate their APIs to this interface.
 */

export interface AnalyticsAdapter {
  /** Track a named event with optional properties. */
  capture(event: string, properties?: Record<string, unknown>): void;

  /** Attach persistent traits to the current user. */
  identify(userId: string, properties?: Record<string, unknown>): void;

  /** Disassociate the current user (e.g. on logout). */
  reset(): void;

  /** Record a page / screen view. */
  page(name?: string, properties?: Record<string, unknown>): void;

  /** Associate the current user with a group (e.g. org / tenant). */
  group(
    groupType: string,
    groupKey: string,
    properties?: Record<string, unknown>
  ): void;

  /** Resolve a single feature flag for the current user. */
  getFeatureFlag(flag: string): boolean | string | undefined;

  /** True when the feature flag evaluates to a truthy value. */
  isFeatureFlagEnabled(flag: string): boolean;

  /** Reload feature flags from the server. */
  reloadFeatureFlags(): void;
}
