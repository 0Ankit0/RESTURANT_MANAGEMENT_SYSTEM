import React from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import FinancesPage from './page';

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const financeHooks = vi.hoisted(() => ({
  useTransactions: vi.fn(),
  useReconcileTransaction: vi.fn(),
  useRetryTransaction: vi.fn(),
}));
vi.mock('@/hooks/use-finances', () => financeHooks);
vi.mock('@/components/finances/stripe-payment-form', () => ({
  PaymentInitiateForm: ({ onSuccess }: { onSuccess: () => void }) => (
    <button onClick={onSuccess}>Mock Payment Success</button>
  ),
}));

describe('FinancesPage', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    financeHooks.useTransactions.mockReturnValue({
      data: [
        {
          id: 1,
          provider: 'khalti',
          amount: 2500,
          currency: 'NPR',
          status: 'pending',
          created_at: '2026-04-01T00:00:00Z',
        },
      ],
      isLoading: false,
    });
    financeHooks.useReconcileTransaction.mockReturnValue({ mutate: vi.fn(), isPending: false });
    financeHooks.useRetryTransaction.mockReturnValue({ mutate: vi.fn(), isPending: false });
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    vi.clearAllMocks();
  });

  it('transitions payment form open and close after success', async () => {
    await act(async () => {
      root.render(<FinancesPage />);
    });

    expect(container.textContent).toContain('Payments');
    expect(container.textContent).toContain('pending');

    const newPaymentButton = Array.from(container.querySelectorAll('button')).find((btn) => btn.textContent?.includes('New Payment'));
    await act(async () => {
      newPaymentButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
    expect(container.textContent).toContain('Initiate Payment');

    const successButton = Array.from(container.querySelectorAll('button')).find((btn) => btn.textContent?.includes('Mock Payment Success'));
    await act(async () => {
      successButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });

    expect(container.textContent).not.toContain('Mock Payment Success');
  });
});
