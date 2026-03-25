'use client';

import { Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/query-client';
import { AnalyticsProvider } from '@/components/analytics/analytics-provider';
import { TemplateRuntimeProvider } from '@/components/runtime/template-runtime-provider';
import { ThemeProvider } from '@/components/theme/theme-provider';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {/* Suspense required because AnalyticsProvider uses useSearchParams */}
      <Suspense>
        <ThemeProvider>
          <AnalyticsProvider>
            <TemplateRuntimeProvider>{children}</TemplateRuntimeProvider>
          </AnalyticsProvider>
        </ThemeProvider>
      </Suspense>
    </QueryClientProvider>
  );
}
