'use client';

import { useEffect } from 'react';
import { applyThemeToDocument, findThemeById } from '@/lib/themes';
import { useThemeStore } from '@/store/theme-store';

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const activeThemeId = useThemeStore((state) => state.activeThemeId);
  const customThemes = useThemeStore((state) => state.customThemes);

  useEffect(() => {
    applyThemeToDocument(findThemeById(activeThemeId, customThemes));
  }, [activeThemeId, customThemes]);

  return children;
}
