import { SignupForm } from '@/components/auth/signup-form';
import { getEnabledProviders } from '@/lib/oauth';

export default async function SignupPage() {
  const enabledProviders = await getEnabledProviders();
  return <SignupForm enabledProviders={enabledProviders} />;
}
