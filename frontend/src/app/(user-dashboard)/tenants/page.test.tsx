import React from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import TenantsPage from './page';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const hooks = vi.hoisted(() => ({
  useTenants: vi.fn(),
  useCreateTenant: vi.fn(),
  useUpdateTenant: vi.fn(),
  useDeleteTenant: vi.fn(),
  useSwitchTenant: vi.fn(),
  useTenantMembers: vi.fn(),
  useUpdateMemberRole: vi.fn(),
  useRemoveMember: vi.fn(),
  useTenantInvitations: vi.fn(),
  useCreateInvitation: vi.fn(),
  useDeleteInvitation: vi.fn(),
  useAcceptInvitation: vi.fn(),
}));

vi.mock('@/hooks/use-tenants', () => hooks);
vi.mock('@/store/auth-store', () => ({
  useAuthStore: () => ({ tenant: { id: 't-1' } }),
}));

function mut() {
  return { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false };
}

describe('TenantsPage', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    hooks.useTenants.mockReturnValue({
      data: {
        items: [{ id: 't-1', name: 'Core Org', slug: 'core-org', description: '', owner_id: 'u-1', is_active: true, created_at: '', updated_at: '' }],
      },
      isLoading: false,
    });
    hooks.useCreateTenant.mockReturnValue(mut());
    hooks.useUpdateTenant.mockReturnValue(mut());
    hooks.useDeleteTenant.mockReturnValue(mut());
    hooks.useSwitchTenant.mockReturnValue(mut());
    hooks.useTenantMembers.mockReturnValue({ data: { items: [] }, isLoading: false });
    hooks.useUpdateMemberRole.mockReturnValue(mut());
    hooks.useRemoveMember.mockReturnValue(mut());
    hooks.useTenantInvitations.mockReturnValue({ data: { items: [] }, isLoading: false });
    hooks.useCreateInvitation.mockReturnValue(mut());
    hooks.useDeleteInvitation.mockReturnValue(mut());
    hooks.useAcceptInvitation.mockReturnValue(mut());
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    vi.clearAllMocks();
  });

  it('renders tenant operations and toggles create form', async () => {
    await act(async () => {
      root.render(<TenantsPage />);
    });

    expect(container.textContent).toContain('Organizations');
    expect(container.textContent).toContain('Core Org');

    const newButton = Array.from(container.querySelectorAll('button')).find((btn) => btn.textContent?.includes('New Organization'));
    expect(newButton).toBeTruthy();
    await act(async () => {
      newButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    expect(container.textContent).toContain('Create Organization');
  });
});
