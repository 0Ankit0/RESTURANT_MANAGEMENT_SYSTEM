'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
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
  const pathname = usePathname();
  const searchParams = useSearchParams();
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
