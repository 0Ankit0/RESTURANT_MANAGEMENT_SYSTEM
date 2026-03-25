'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateTenant, useUpdateTenant } from '@/hooks/use-tenants';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import type { Tenant } from '@/types';

const tenantSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  slug: z
    .string()
    .min(1, 'Slug is required')
    .max(100)
    .regex(/^[a-z0-9-]+$/, 'Slug may only contain lowercase letters, digits, and hyphens'),
  description: z.string().max(500).optional(),
});

type TenantFormData = z.infer<typeof tenantSchema>;

interface TenantFormProps {
  tenant?: Tenant;
  onSuccess?: (tenant: Tenant) => void;
  onCancel?: () => void;
}

export function TenantForm({ tenant, onSuccess, onCancel }: TenantFormProps) {
  const createTenant = useCreateTenant();
  const updateTenant = useUpdateTenant();
  const isEditing = !!tenant;

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<TenantFormData>({
    resolver: zodResolver(tenantSchema),
    defaultValues: {
      name: tenant?.name ?? '',
      slug: tenant?.slug ?? '',
      description: tenant?.description ?? '',
    },
  });

  // Auto-generate slug from name when creating
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!isEditing) {
      setValue('slug', e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''));
    }
  };

  const onSubmit = async (data: TenantFormData) => {
    try {
      let result: Tenant;
      if (isEditing) {
        result = await updateTenant.mutateAsync({ id: tenant.id, data });
      } else {
        result = await createTenant.mutateAsync(data);
      }
      onSuccess?.(result);
    } catch (error) {
      console.error('Error saving tenant:', error);
    }
  };

  const isLoading = createTenant.isPending || updateTenant.isPending;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEditing ? 'Edit Organisation' : 'Create Organisation'}</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Name"
            {...register('name', { onChange: handleNameChange })}
            error={errors.name?.message}
            placeholder="My Organisation"
          />
          <Input
            label="Slug"
            {...register('slug')}
            error={errors.slug?.message}
            placeholder="my-organisation"
          />
          <Input
            label="Description (optional)"
            {...register('description')}
            error={errors.description?.message}
            placeholder="What is this organisation for?"
          />
          <div className="flex gap-4">
            <Button type="submit" isLoading={isLoading}>
              {isEditing ? 'Save Changes' : 'Create Organisation'}
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
