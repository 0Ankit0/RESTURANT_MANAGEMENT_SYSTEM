export type OAuthProvider = 'google' | 'github' | 'facebook';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

// ---------------------------------------------------------------------------
// Client-side: open OAuth popup
// ---------------------------------------------------------------------------

/** Opens an OAuth provider popup. Must be called from a browser context. */
export function startOAuthLogin(provider: OAuthProvider) {
  const state = crypto.randomUUID();
  sessionStorage.setItem('oauth_state', state);

  const authUrl = `${BACKEND_URL}/auth/social/${provider}/?state=${state}`;

  const width = 500;
  const height = 600;
  const left = window.screen.width / 2 - width / 2;
  const top = window.screen.height / 2 - height / 2;

  window.open(
    authUrl,
    `Sign in with ${provider}`,
    `width=${width},height=${height},left=${left},top=${top}`,
  );
}

// ---------------------------------------------------------------------------
// Server-side: fetch enabled providers
// Called from Server Component pages — never from client components directly.
// Next.js caches this fetch; providers only change when the backend restarts.
// ---------------------------------------------------------------------------

/** Returns the list of providers currently enabled on the backend. */
export async function getEnabledProviders(): Promise<OAuthProvider[]> {
  try {
    const res = await fetch(`${BACKEND_URL}/auth/social/providers/`, {
      // Revalidate every hour — providers are static config, not runtime data.
      next: { revalidate: 3600 },
    });
    if (!res.ok) return [];
    const data = (await res.json()) as { providers: string[] };
    return (data.providers ?? []) as OAuthProvider[];
  } catch {
    return [];
  }
}
