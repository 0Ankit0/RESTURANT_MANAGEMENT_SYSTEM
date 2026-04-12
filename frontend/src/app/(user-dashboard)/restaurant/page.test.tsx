import React from 'react';
import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import RestaurantOpsPage, { deriveStaffContext, nextTicketStatus } from './page';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const { mockCapture, mockState, hookMocks } = vi.hoisted(() => ({
  mockCapture: vi.fn(),
  mockState: {
    user: { id: 'user-44', staff_id: null, branch_memberships: [{ branch_id: 2 }] },
  },
  hookMocks: {
  useRestaurantBranches: vi.fn(),
  useBranchTables: vi.fn(),
  useBranchOrders: vi.fn(),
  useBranchBills: vi.fn(),
  useBranchWaitlist: vi.fn(),
  useBranchMenuItems: vi.fn(),
  useBranchReservations: vi.fn(),
  useKitchenTickets: vi.fn(),
  useOperationalNotifications: vi.fn(),
  useBranchOperationsReport: vi.fn(),
  useCreateReservation: vi.fn(),
  useSeatTable: vi.fn(),
  usePromoteWaitlist: vi.fn(),
  useCreateOrder: vi.fn(),
  useUpdateKitchenTicket: vi.fn(),
  useCreateOrderEditApproval: vi.fn(),
  useResolveOrderEditApproval: vi.fn(),
  useUpdateOrder: vi.fn(),
  useSettleBill: vi.fn(),
  useCancelReservation: vi.fn(),
  useTransitionReservation: vi.fn(),
},
}));

vi.mock('@/hooks/use-restaurant', () => hookMocks);
vi.mock('@/hooks/use-analytics', () => ({ useAnalytics: () => ({ capture: mockCapture }) }));
vi.mock('@/hooks/use-websocket', () => ({ useRestaurantOpsWebSocket: vi.fn() }));
vi.mock('@/store/auth-store', () => ({ useAuthStore: (selector: (s: typeof mockState) => unknown) => selector(mockState) }));

function qState(data: unknown) {
  return { data, refetch: vi.fn() };
}

function mState() {
  return { mutateAsync: vi.fn(), isPending: false };
}

describe('RestaurantOpsPage', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    hookMocks.useRestaurantBranches.mockReturnValue(qState([
      { id: 1, name: 'Main', tax_rate: 0.1, service_charge_rate: 0.1, is_active: true },
      { id: 2, name: 'Downtown', tax_rate: 0.1, service_charge_rate: 0.1, is_active: true },
    ]));
    hookMocks.useBranchTables.mockReturnValue(qState([]));
    hookMocks.useBranchOrders.mockReturnValue(qState({ items: [], next_cursor: null }));
    hookMocks.useBranchBills.mockReturnValue(qState([]));
    hookMocks.useBranchWaitlist.mockReturnValue(qState({ items: [], next_cursor: null }));
    hookMocks.useBranchMenuItems.mockReturnValue(qState([]));
    hookMocks.useBranchReservations.mockReturnValue(qState([]));
    hookMocks.useKitchenTickets.mockReturnValue(qState({ items: [], next_cursor: null }));
    hookMocks.useOperationalNotifications.mockReturnValue(qState([]));
    hookMocks.useBranchOperationsReport.mockReturnValue(qState({
      orders_count: 0,
      open_tickets: 0,
      gross_sales: 0,
      low_stock_count: 0,
      settlement_health: { open_drawers: 0, unpaid_bills: 0, failed_exports: 0 },
    }));
    hookMocks.useCreateReservation.mockReturnValue(mState());
    hookMocks.useSeatTable.mockReturnValue(mState());
    hookMocks.usePromoteWaitlist.mockReturnValue(mState());
    hookMocks.useCreateOrder.mockReturnValue(mState());
    hookMocks.useUpdateKitchenTicket.mockReturnValue(mState());
    hookMocks.useCreateOrderEditApproval.mockReturnValue(mState());
    hookMocks.useResolveOrderEditApproval.mockReturnValue(mState());
    hookMocks.useUpdateOrder.mockReturnValue(mState());
    hookMocks.useSettleBill.mockReturnValue(mState());
    hookMocks.useCancelReservation.mockReturnValue(mState());
    hookMocks.useTransitionReservation.mockReturnValue(mState());
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    vi.clearAllMocks();
  });

  it('derives staff/branch context and transitions', () => {
    expect(
      deriveStaffContext({
        id: '7',
        staff_id: 14,
        memberships: [{ home_branch_id: 3 }, { branch: { id: 9 } }],
      })
    ).toEqual({ staffId: 14, branchPreferences: [3, 9] });
    expect(nextTicketStatus('queued')).toBe('in_preparation');
    expect(nextTicketStatus('served')).toBeNull();
  });

  it('limits branch options by membership and blocks staff actions without staff profile', async () => {
    await act(async () => {
      root.render(<RestaurantOpsPage />);
    });

    const options = Array.from(container.querySelectorAll('select option')).map((o) => o.textContent);
    expect(options).toEqual(['Downtown (#2)']);
    expect(container.textContent).toContain('No eligible staff profile is linked to your user.');
  });

  it('shows action errors for unavailable seat/waitlist/settlement flows', async () => {
    await act(async () => {
      root.render(<RestaurantOpsPage />);
    });

    const clickByText = async (label: string) => {
      const button = Array.from(container.querySelectorAll('button')).find((btn) => btn.textContent?.includes(label));
      expect(button).toBeTruthy();
      await act(async () => {
        button?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      });
    };

    await clickByText('Seat First Available Table');
    expect(container.textContent).toContain('No available table to seat right now.');

    await clickByText('Promote First Waitlist');
    expect(container.textContent).toContain('Need one waiting guest and one available table for promotion.');

    await clickByText('Settle First Open Bill');
    expect(container.textContent).toContain('No unsettled bill available.');
  });
});
