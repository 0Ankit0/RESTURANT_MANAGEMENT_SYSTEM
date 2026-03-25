import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';
import { THEME_PRESETS } from '@/lib/themes';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Fastapi Template',
  description: 'Modern Fastapi Template platform',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const serializedThemes = JSON.stringify(THEME_PRESETS);

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var presets = ${serializedThemes};
                  var storedTheme = localStorage.getItem('theme-storage');
                  var activeThemeId = presets[0].id;
                  var customThemes = [];
                  if (storedTheme) {
                    var parsed = JSON.parse(storedTheme);
                    if (parsed && parsed.state) {
                      if (typeof parsed.state.activeThemeId === 'string') {
                        activeThemeId = parsed.state.activeThemeId;
                      }
                      if (Array.isArray(parsed.state.customThemes)) {
                        customThemes = parsed.state.customThemes;
                      }
                    }
                  }
                  var themes = presets.concat(customThemes);
                  var activeTheme = themes.find(function(theme) { return theme.id === activeThemeId; }) || presets[0];
                  var root = document.documentElement;
                  root.dataset.themeId = activeTheme.id;
                  root.dataset.themeMode = activeTheme.mode;
                  root.style.colorScheme = activeTheme.mode;
                  Object.entries(activeTheme.palette).forEach(function(entry) {
                    var cssName = entry[0].replace(/[A-Z]/g, function(letter) {
                      return '-' + letter.toLowerCase();
                    });
                    root.style.setProperty('--' + cssName, entry[1]);
                  });
                } catch (error) {
                  document.documentElement.dataset.themeMode = 'light';
                }
              })();
            `,
          }}
        />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
