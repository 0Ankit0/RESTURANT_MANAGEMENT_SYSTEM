import { describe, expect, it, vi } from 'vitest';
import { AnalyticsService } from './service';
import type { AnalyticsAdapter } from './interface';

function createAdapter(): AnalyticsAdapter {
  return {
    capture: vi.fn(),
    identify: vi.fn(),
    reset: vi.fn(),
    page: vi.fn(),
    group: vi.fn(),
    getFeatureFlag: vi.fn().mockReturnValue(true),
    isFeatureFlagEnabled: vi.fn().mockReturnValue(true),
    reloadFeatureFlags: vi.fn(),
  };
}

describe('AnalyticsService', () => {
  it('delegates to the active adapter', () => {
    const adapter = createAdapter();
    const service = new AnalyticsService(adapter);

    service.capture('template_loaded', { mode: 'test' });
    service.identify('42', { role: 'admin' });
    service.page('dashboard');
    service.group('tenant', 'core');

    expect(adapter.capture).toHaveBeenCalledWith('template_loaded', { mode: 'test' });
    expect(adapter.identify).toHaveBeenCalledWith('42', { role: 'admin' });
    expect(adapter.page).toHaveBeenCalledWith('dashboard', undefined);
    expect(adapter.group).toHaveBeenCalledWith('tenant', 'core', undefined);
  });

  it('stays safe when analytics is disabled', () => {
    const service = new AnalyticsService(null);

    expect(() => service.capture('noop')).not.toThrow();
    expect(service.enabled).toBe(false);
    expect(service.isFeatureFlagEnabled('missing')).toBe(false);
  });
});
