import { LoginForm } from '@/components/auth/login-form';
import { getEnabledProviders } from '@/lib/oauth';

export default async function LoginPage() {
  const enabledProviders = await getEnabledProviders();
  return <LoginForm enabledProviders={enabledProviders} />;
}
