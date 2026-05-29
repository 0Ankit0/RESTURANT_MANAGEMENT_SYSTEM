import { useEffect, useState } from 'react';
import { SignupForm } from '@/components/auth/signup-form';
import { getEnabledProviders } from '@/lib/oauth';
import type { OAuthProvider } from '@/lib/oauth';

export default function SignupPage() {
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

  return <SignupForm enabledProviders={enabledProviders} />;
}
