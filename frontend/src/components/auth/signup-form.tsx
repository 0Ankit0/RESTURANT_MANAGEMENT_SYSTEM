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

const PROVIDER_LABELS: Record<OAuthProvider, string> = {
  google: 'Google',
  github: 'GitHub',
  facebook: 'Facebook',
};

const signupSchema = z
  .object({
    username: z.string().min(3, 'Username must be at least 3 characters'),
    email: z.string().email('Please enter a valid email address'),
    first_name: z.string().optional(),
    last_name: z.string().optional(),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Must contain at least one digit'),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  });

type SignupFormData = z.infer<typeof signupSchema>;

interface SignupFormProps {
  enabledProviders: OAuthProvider[];
}

export function SignupForm({ enabledProviders }: SignupFormProps) {
  const router = useRouter();
  const { signupAsync, isLoading, signupError } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
  });

  const onSubmit = async (data: SignupFormData) => {
    try {
      await signupAsync(data);
      router.push('/dashboard');
    } catch {
      // error shown via signupError
    }
  };

  const getErrorMessage = () => {
    if (!signupError) return null;
    const err = signupError as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail || 'Failed to create account. Please try again.';
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle>Create an account</CardTitle>
        <CardDescription>Get started with your free account</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {signupError && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
              {getErrorMessage()}
            </div>
          )}
          <Input
            id="username"
            label="Username"
            placeholder="your_username"
            {...register('username')}
            error={errors.username?.message}
          />
          <Input
            id="email"
            type="email"
            label="Email"
            placeholder="you@example.com"
            {...register('email')}
            error={errors.email?.message}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              id="first_name"
              label="First name"
              placeholder="John"
              {...register('first_name')}
              error={errors.first_name?.message}
            />
            <Input
              id="last_name"
              label="Last name"
              placeholder="Doe"
              {...register('last_name')}
              error={errors.last_name?.message}
            />
          </div>
          <Input
            id="password"
            type="password"
            label="Password"
            placeholder="••••••••"
            {...register('password')}
            error={errors.password?.message}
          />
          <Input
            id="confirm_password"
            type="password"
            label="Confirm password"
            placeholder="••••••••"
            {...register('confirm_password')}
            error={errors.confirm_password?.message}
          />
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button type="submit" className="w-full" isLoading={isLoading}>
            Create account
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
            Already have an account?{' '}
            <Link href="/login" className="text-blue-600 hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
