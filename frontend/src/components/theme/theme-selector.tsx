'use client';

import { Palette } from 'lucide-react';
import { getAllThemes } from '@/lib/themes';
import { useThemeStore } from '@/store/theme-store';

export function ThemeSelector() {
  const activeThemeId = useThemeStore((state) => state.activeThemeId);
  const customThemes = useThemeStore((state) => state.customThemes);
  const setActiveTheme = useThemeStore((state) => state.setActiveTheme);
  const themes = getAllThemes(customThemes);

  return (
    <label className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700">
      <Palette className="h-4 w-4 text-[var(--accent)]" />
      <span className="text-xs font-medium uppercase tracking-[0.18em] text-gray-400">
        Theme
      </span>
      <select
        value={activeThemeId}
        onChange={(event) => setActiveTheme(event.target.value)}
        className="min-w-32 bg-transparent text-sm font-medium text-gray-700 outline-none"
        aria-label="Select theme"
      >
        {themes.map((theme) => (
          <option key={theme.id} value={theme.id}>
            {theme.name}
            {theme.isCustom ? ' (Custom)' : ''}
          </option>
        ))}
      </select>
    </label>
  );
}
