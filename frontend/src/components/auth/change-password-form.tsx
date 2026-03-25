'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Lock, CheckCircle } from 'lucide-react';
import { useChangePassword } from '@/hooks/use-auth';

const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
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

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export function ChangePasswordForm() {
  const [success, setSuccess] = useState(false);
  const changePassword = useChangePassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  });

  const onSubmit = (data: ChangePasswordFormData) => {
    setSuccess(false);
    changePassword.mutate(data, {
      onSuccess: () => {
        setSuccess(true);
        reset();
      },
    });
  };

  const getErrorMessage = () => {
    if (!changePassword.error) return null;
    const err = changePassword.error as { response?: { data?: { detail?: string } } };
    return err?.response?.data?.detail || 'Failed to change password. Please try again.';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="h-5 w-5" />
          Change Password
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {changePassword.error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
              {getErrorMessage()}
            </div>
          )}
          {success && (
            <div className="p-3 text-sm text-green-600 bg-green-50 rounded-lg flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Password changed successfully!
            </div>
          )}
          <Input
            id="current_password"
            type="password"
            label="Current Password"
            placeholder="Enter current password"
            {...register('current_password')}
            error={errors.current_password?.message}
          />
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
            label="Confirm New Password"
            placeholder="Confirm new password"
            {...register('confirm_password')}
            error={errors.confirm_password?.message}
          />
          <Button type="submit" isLoading={changePassword.isPending}>
            Change Password
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
