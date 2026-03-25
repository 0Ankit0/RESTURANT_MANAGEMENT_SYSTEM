'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';
import { startOAuthLogin, type OAuthProvider } from '@/lib/oauth';
import type { OTPLoginResponse } from '@/types';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const PROVIDER_LABELS: Record<OAuthProvider, string> = {
  google: 'Google',
  github: 'GitHub',
  facebook: 'Facebook',
};

interface LoginFormProps {
  enabledProviders: OAuthProvider[];
}

export function LoginForm({ enabledProviders }: LoginFormProps) {
  const router = useRouter();
  const { loginAsync, isLoading, loginError } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      const result = await loginAsync(data);
      if (result && 'requires_otp' in result) {
        const otpResult = result as OTPLoginResponse;
        router.push(`/otp-verify?temp_token=${otpResult.temp_token}`);
      } else {
        router.push('/dashboard');
      }
    } catch {
      // error shown via loginError
    }
  };

  const getErrorMessage = () => {
    if (!loginError) return null;
    const err = loginError as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail || 'Invalid username or password. Please try again.';
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle>Welcome back</CardTitle>
        <CardDescription>Sign in to your account to continue</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {loginError && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
              {getErrorMessage()}
            </div>
          )}
          <Input
            id="username"
            type="text"
            label="Username"
            placeholder="your_username"
            {...register('username')}
            error={errors.username?.message}
          />
          <Input
            id="password"
            type="password"
            label="Password"
            placeholder="••••••••"
            {...register('password')}
            error={errors.password?.message}
          />
          <div className="flex items-center justify-end">
            <Link href="/forgot-password" className="text-sm text-blue-600 hover:underline">
              Forgot password?
            </Link>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button type="submit" className="w-full" isLoading={isLoading}>
            Sign in
          </Button>

          {enabledProviders.length > 0 && (
            <>
              <div className="relative w-full">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-gray-500">Or continue with</span>
                </div>
              </div>

              <div
                className="grid gap-3 w-full"
                style={{ gridTemplateColumns: `repeat(${enabledProviders.length}, minmax(0, 1fr))` }}
              >
                {enabledProviders.map((provider) => (
                  <Button
                    key={provider}
                    variant="outline"
                    type="button"
                    onClick={() => startOAuthLogin(provider)}
                  >
                    {PROVIDER_LABELS[provider]}
                  </Button>
                ))}
              </div>
            </>
          )}

          <p className="text-sm text-center text-gray-600">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="text-blue-600 hover:underline">
              Sign up
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
