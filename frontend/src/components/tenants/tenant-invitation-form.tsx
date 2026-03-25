'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateInvitation } from '@/hooks/use-tenants';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Mail, UserPlus } from 'lucide-react';

const invitationSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  role: z.enum(['admin', 'member']),
});

type InvitationFormData = z.infer<typeof invitationSchema>;

interface TenantInvitationFormProps {
  tenantId: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function TenantInvitationForm({ tenantId, onSuccess, onCancel }: TenantInvitationFormProps) {
  const inviteMember = useCreateInvitation();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<InvitationFormData>({
    resolver: zodResolver(invitationSchema),
    defaultValues: {
      email: '',
      role: 'member',
    },
  });

  const onSubmit = async (data: InvitationFormData) => {
    try {
      await inviteMember.mutateAsync({
        tenantId,
        data: { email: data.email, role: data.role as import('@/types').TenantRole },
      });
      reset();
      onSuccess?.();
    } catch (error) {
      console.error('Error inviting member:', error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <UserPlus className="h-5 w-5" />
          Invite Team Member
        </CardTitle>
        <CardDescription>Send an invitation to join your organization</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Input
              type="email"
              label="Email Address"
              placeholder="colleague@company.com"
              {...register('email')}
              error={errors.email?.message}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <select
              {...register('role')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="member">Member - Can view and use resources</option>
              <option value="admin">Admin - Can manage team and settings</option>
            </select>
            {errors.role && <p className="mt-1 text-sm text-red-600">{errors.role.message}</p>}
          </div>

          <div className="flex gap-4">
            <Button type="submit" isLoading={inviteMember.isPending}>
              <Mail className="h-4 w-4 mr-2" />
              Send Invitation
            </Button>
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
