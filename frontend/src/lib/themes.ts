export type ThemeMode = 'light' | 'dark';

export interface ThemePalette {
  background: string;
  foreground: string;
  surface: string;
  surfaceMuted: string;
  surfaceSubtle: string;
  borderColor: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  accentForeground: string;
  accentSoft: string;
  successSoft: string;
  warningSoft: string;
  dangerSoft: string;
}

export interface AppTheme {
  id: string;
  name: string;
  mode: ThemeMode;
  palette: ThemePalette;
  isCustom?: boolean;
}

export interface CustomThemeDraft {
  name: string;
  mode: ThemeMode;
  background: string;
  surface: string;
  textPrimary: string;
  accent: string;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function normalizeHex(hex: string) {
  const cleaned = hex.trim().replace('#', '');
  if (cleaned.length === 3) {
    return `#${cleaned.split('').map((char) => `${char}${char}`).join('')}`.toLowerCase();
  }
  if (cleaned.length === 6) {
    return `#${cleaned}`.toLowerCase();
  }
  return '#2563eb';
}

function hexToRgb(hex: string) {
  const normalized = normalizeHex(hex).slice(1);
  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  };
}

function rgbToHex(r: number, g: number, b: number) {
  return `#${[r, g, b]
    .map((value) => clamp(Math.round(value), 0, 255).toString(16).padStart(2, '0'))
    .join('')}`;
}

function mixColors(base: string, blend: string, weight: number) {
  const start = hexToRgb(base);
  const end = hexToRgb(blend);
  const ratio = clamp(weight, 0, 1);

  return rgbToHex(
    start.r + (end.r - start.r) * ratio,
    start.g + (end.g - start.g) * ratio,
    start.b + (end.b - start.b) * ratio
  );
}

function readableText(background: string) {
  const { r, g, b } = hexToRgb(background);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6 ? '#0f172a' : '#f8fafc';
}

export function buildTheme(theme: {
  id: string;
  name: string;
  mode: ThemeMode;
  background: string;
  surface: string;
  textPrimary: string;
  accent: string;
  isCustom?: boolean;
}): AppTheme {
  const background = normalizeHex(theme.background);
  const surface = normalizeHex(theme.surface);
  const textPrimary = normalizeHex(theme.textPrimary);
  const accent = normalizeHex(theme.accent);
  const blendBase = theme.mode === 'dark' ? '#ffffff' : '#0f172a';

  return {
    id: theme.id,
    name: theme.name,
    mode: theme.mode,
    isCustom: theme.isCustom,
    palette: {
      background,
      foreground: textPrimary,
      surface,
      surfaceMuted: mixColors(background, blendBase, theme.mode === 'dark' ? 0.04 : 0.03),
      surfaceSubtle: mixColors(surface, blendBase, theme.mode === 'dark' ? 0.06 : 0.05),
      borderColor: mixColors(surface, blendBase, theme.mode === 'dark' ? 0.14 : 0.12),
      textPrimary,
      textSecondary: mixColors(textPrimary, background, theme.mode === 'dark' ? 0.22 : 0.3),
      textMuted: mixColors(textPrimary, background, theme.mode === 'dark' ? 0.42 : 0.5),
      accent,
      accentForeground: readableText(accent),
      accentSoft: mixColors(accent, background, theme.mode === 'dark' ? 0.8 : 0.88),
      successSoft: mixColors('#16a34a', background, theme.mode === 'dark' ? 0.82 : 0.9),
      warningSoft: mixColors('#d97706', background, theme.mode === 'dark' ? 0.84 : 0.9),
      dangerSoft: mixColors('#dc2626', background, theme.mode === 'dark' ? 0.84 : 0.9),
    },
  };
}

export const THEME_PRESETS: AppTheme[] = [
  buildTheme({
    id: 'skyline',
    name: 'Skyline',
    mode: 'light',
    background: '#f8fafc',
    surface: '#ffffff',
    textPrimary: '#0f172a',
    accent: '#2563eb',
  }),
  buildTheme({
    id: 'midnight',
    name: 'Midnight',
    mode: 'dark',
    background: '#020617',
    surface: '#0f172a',
    textPrimary: '#e2e8f0',
    accent: '#38bdf8',
  }),
  buildTheme({
    id: 'forest',
    name: 'Forest',
    mode: 'light',
    background: '#f4fbf6',
    surface: '#ffffff',
    textPrimary: '#163020',
    accent: '#15803d',
  }),
  buildTheme({
    id: 'ember',
    name: 'Ember',
    mode: 'dark',
    background: '#1c1917',
    surface: '#292524',
    textPrimary: '#f5f5f4',
    accent: '#f97316',
  }),
];

export const DEFAULT_THEME_ID = THEME_PRESETS[0].id;

export function getAllThemes(customThemes: AppTheme[]) {
  return [...THEME_PRESETS, ...customThemes];
}

export function findThemeById(activeThemeId: string, customThemes: AppTheme[]) {
  return getAllThemes(customThemes).find((theme) => theme.id === activeThemeId) ?? THEME_PRESETS[0];
}

export function createCustomTheme(draft: CustomThemeDraft) {
  return buildTheme({
    id: `custom-${Date.now()}`,
    name: draft.name.trim() || 'Custom Theme',
    mode: draft.mode,
    background: draft.background,
    surface: draft.surface,
    textPrimary: draft.textPrimary,
    accent: draft.accent,
    isCustom: true,
  });
}

export function applyThemeToDocument(theme: AppTheme) {
  const root = document.documentElement;
  root.dataset.themeId = theme.id;
  root.dataset.themeMode = theme.mode;
  root.style.colorScheme = theme.mode;

  Object.entries(theme.palette).forEach(([key, value]) => {
    const cssName = key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
    root.style.setProperty(`--${cssName}`, value);
  });
}
