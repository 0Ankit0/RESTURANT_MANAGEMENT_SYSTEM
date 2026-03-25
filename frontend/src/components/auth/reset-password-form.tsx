'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useRouter, useSearchParams } from 'next/navigation';
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
import { useConfirmPasswordReset } from '@/hooks/use-auth';

const resetPasswordSchema = z
  .object({
    new_password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Must contain at least one digit'),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('t') ?? '';
  const confirmReset = useConfirmPasswordReset();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = (data: ResetPasswordFormData) => {
    confirmReset.mutate(
      { token, ...data },
      { onSuccess: () => router.push('/login?reset=success') }
    );
  };

  const getErrorMessage = () => {
    if (!confirmReset.error) return null;
    const err = confirmReset.error as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail || 'Failed to reset password. The link may have expired.';
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle>Reset password</CardTitle>
        <CardDescription>Enter your new password below.</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {confirmReset.error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
              {getErrorMessage()}
            </div>
          )}
          <Input
            id="new_password"
            type="password"
            label="New Password"
            placeholder="Minimum 8 characters"
            {...register('new_password')}
            error={errors.new_password?.message}
          />
          <Input
            id="confirm_password"
            type="password"
            label="Confirm Password"
            placeholder="Confirm new password"
            {...register('confirm_password')}
            error={errors.confirm_password?.message}
          />
        </CardContent>
        <CardFooter>
          <Button type="submit" className="w-full" isLoading={confirmReset.isPending}>
            Reset Password
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
