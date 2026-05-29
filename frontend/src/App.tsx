import { RouterProvider } from 'react-router-dom';
import { useEffect } from 'react';
import { Providers } from '@/components/providers';
import { appRouter } from '@/router';
import { THEME_PRESETS } from '@/lib/themes';
import { preloadCriticalRoutes } from '@/route-preload';

function ThemeBootstrap() {
  useEffect(() => {
    try {
      const presets = THEME_PRESETS;
      const storedTheme = localStorage.getItem('theme-storage');
      let activeThemeId = presets[0].id;
      let customThemes: typeof THEME_PRESETS = [];

      if (storedTheme) {
        const parsed = JSON.parse(storedTheme) as {
          state?: { activeThemeId?: string; customThemes?: typeof THEME_PRESETS };
        };
        if (parsed?.state?.activeThemeId) {
          activeThemeId = parsed.state.activeThemeId;
        }
        if (Array.isArray(parsed?.state?.customThemes)) {
          customThemes = parsed.state.customThemes;
        }
      }

      const themes = presets.concat(customThemes);
      const activeTheme = themes.find((theme) => theme.id === activeThemeId) ?? presets[0];
      const root = document.documentElement;
      root.dataset.themeId = activeTheme.id;
      root.dataset.themeMode = activeTheme.mode;
      root.style.colorScheme = activeTheme.mode;

      Object.entries(activeTheme.palette).forEach(([key, value]) => {
        const cssName = key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
        root.style.setProperty(`--${cssName}`, value);
      });
    } catch {
      document.documentElement.dataset.themeMode = 'light';
    }
  }, []);

  return null;
}

export function App() {
  useEffect(() => {
    let idleCallback: number;
    let timeoutHandle: number | null = null;

    if (typeof window.requestIdleCallback === 'function') {
      idleCallback = window.requestIdleCallback(() => preloadCriticalRoutes());
    } else {
      timeoutHandle = window.setTimeout(() => preloadCriticalRoutes(), 250);
      idleCallback = -1;
    }

    return () => {
      if (idleCallback !== -1 && typeof window.cancelIdleCallback === 'function') {
        window.cancelIdleCallback(idleCallback);
      }

      if (timeoutHandle !== null) {
        window.clearTimeout(timeoutHandle);
      }
    };
  }, []);

  return (
    <Providers>
      <ThemeBootstrap />
      <RouterProvider router={appRouter} />
    </Providers>
  );
}
