import React from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import RBACPage from './page';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const hooks = vi.hoisted(() => ({
  useRoles: vi.fn(),
  usePermissions: vi.fn(),
  useCreateRole: vi.fn(),
  useCreatePermission: vi.fn(),
  useSecurityIncidents: vi.fn(),
}));

vi.mock('@/hooks/use-rbac', () => hooks);
vi.mock('@/hooks/use-observability', () => ({ useSecurityIncidents: hooks.useSecurityIncidents }));
vi.mock('./user-roles-tab', () => ({ UserRolesTab: () => <div data-testid="user-roles-tab">assignments-body</div> }));

function mut() {
  return { mutate: vi.fn(), isPending: false };
}

describe('RBACPage', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    hooks.useRoles.mockReturnValue({ data: { items: [{ id: 1, name: 'admin', description: 'full access', created_at: '2026-04-01T00:00:00Z' }] }, isLoading: false });
    hooks.usePermissions.mockReturnValue({ data: { items: [{ id: 1, resource: 'orders', action: 'manage', description: 'manage orders' }] }, isLoading: false });
    hooks.useCreateRole.mockReturnValue(mut());
    hooks.useCreatePermission.mockReturnValue(mut());
    hooks.useSecurityIncidents.mockReturnValue({ data: { items: [{ id: 'i1', status: 'open', summary: 'role changed', last_seen_at: '2026-04-01T01:00:00Z' }] }, isLoading: false });
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    vi.clearAllMocks();
  });

  it('switches between roles, assignments, and audit views', async () => {
    await act(async () => {
      root.render(<RBACPage />);
    });

    expect(container.textContent).toContain('Roles & Permissions');
    expect(container.textContent).toContain('admin');

    const assignmentsTab = Array.from(container.querySelectorAll('button')).find((btn) => btn.textContent?.includes('Assignments'));
    await act(async () => assignmentsTab?.dispatchEvent(new MouseEvent('click', { bubbles: true })));
    expect(container.textContent).toContain('assignments-body');

    const auditTab = Array.from(container.querySelectorAll('button')).find((btn) => btn.textContent?.includes('Audit'));
    await act(async () => auditTab?.dispatchEvent(new MouseEvent('click', { bubbles: true })));
    expect(container.textContent).toContain('role changed');
  });
});
