import { useEffect, useState } from 'react';
import { LoginForm } from '@/components/auth/login-form';
import { getEnabledProviders } from '@/lib/oauth';
import type { OAuthProvider } from '@/lib/oauth';

export default function LoginPage() {
  const [enabledProviders, setEnabledProviders] = useState<OAuthProvider[]>([]);

  useEffect(() => {
    let cancelled = false;

    void getEnabledProviders().then((providers) => {
      if (!cancelled) {
        setEnabledProviders(providers);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return <LoginForm enabledProviders={enabledProviders} />;
}
