import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  type AppTheme,
  type CustomThemeDraft,
  DEFAULT_THEME_ID,
  createCustomTheme,
  findThemeById,
} from '@/lib/themes';

interface ThemeState {
  activeThemeId: string;
  customThemes: AppTheme[];
  setActiveTheme: (themeId: string) => void;
  addCustomTheme: (draft: CustomThemeDraft) => AppTheme;
  deleteCustomTheme: (themeId: string) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      activeThemeId: DEFAULT_THEME_ID,
      customThemes: [],
      setActiveTheme: (activeThemeId) => set({ activeThemeId }),
      addCustomTheme: (draft) => {
        const customTheme = createCustomTheme(draft);
        set((state) => ({
          activeThemeId: customTheme.id,
          customThemes: [...state.customThemes, customTheme],
        }));
        return customTheme;
      },
      deleteCustomTheme: (themeId) => {
        set((state) => {
          const nextThemes = state.customThemes.filter((theme) => theme.id !== themeId);
          const nextActiveTheme =
            state.activeThemeId === themeId
              ? findThemeById(DEFAULT_THEME_ID, nextThemes).id
              : state.activeThemeId;
          return {
            activeThemeId: nextActiveTheme,
            customThemes: nextThemes,
          };
        });
      },
    }),
    {
      name: 'theme-storage',
    }
  )
);
