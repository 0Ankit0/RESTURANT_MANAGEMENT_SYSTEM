'use client';

import { useEffect, useMemo, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { analytics } from '@/lib/analytics';

/**
 * AnalyticsProvider
 *
 * Drop this inside your Providers component.  It automatically tracks page
 * views whenever the Next.js router path changes, so individual pages don't
 * need to call analytics.page() manually.
 *
 * Renders nothing — purely a side-effect component.
 */
export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const pathname = location.pathname;
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (!analytics.enabled) return;

    // Skip the very first render — posthog fires pageview on init itself
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const url = pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '');
    analytics.page(pathname, { url });
  }, [pathname, searchParams]);

  return <>{children}</>;
}
