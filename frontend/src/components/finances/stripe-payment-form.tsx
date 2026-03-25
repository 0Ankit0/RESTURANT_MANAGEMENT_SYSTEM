'use client';

import { useState } from 'react';
import { useInitiatePayment, usePaymentProviders } from '@/hooks/use-finances';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ExternalLink } from 'lucide-react';
import type { PaymentProvider, InitiatePaymentResponse } from '@/types';

interface PaymentInitiateFormProps {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

/** Auto-submit a hidden HTML form — required for eSewa's form-POST flow. */
function submitHiddenForm(action: string, fields: Record<string, unknown>) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = action;
  form.target = '_self';
  Object.entries(fields).forEach(([name, value]) => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = String(value ?? '');
    form.appendChild(input);
  });
  document.body.appendChild(form);
  form.submit();
}

export function PaymentInitiateForm({ onSuccess, onError }: PaymentInitiateFormProps) {
  const [selectedProvider, setSelectedProvider] = useState<PaymentProvider | ''>('');
  const [amountNpr, setAmountNpr] = useState('');
  const [orderName, setOrderName] = useState('');
  // Stable order ID per form mount — user can refresh page for a new one
  const [orderId] = useState(() => `ORDER-${Date.now()}`);
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');

  const { data: providers, isLoading: loadingProviders } = usePaymentProviders();
  const initiatePayment = useInitiatePayment();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProvider || !amountNpr || !orderName) return;

    const nprAmount = parseFloat(amountNpr);
    if (isNaN(nprAmount) || nprAmount <= 0) return;

    // Khalti expects paisa (1 NPR = 100 paisa); eSewa expects NPR directly
    const amount =
      selectedProvider === 'khalti' ? Math.round(nprAmount * 100) : Math.round(nprAmount);

    const returnUrl = `${window.location.origin}/payment-callback?provider=${selectedProvider}`;

    const payload = {
      provider: selectedProvider as PaymentProvider,
      amount,
      purchase_order_id: orderId,
      purchase_order_name: orderName,
      return_url: returnUrl,
      website_url: window.location.origin,
      customer_name: customerName || undefined,
      customer_email: customerEmail || undefined,
      customer_phone: customerPhone || undefined,
    };

    initiatePayment.mutate(payload, {
      onSuccess: (data: InitiatePaymentResponse) => {
        if (selectedProvider === 'esewa' && data.extra?.form_fields) {
          // eSewa requires an HTML form POST — auto-submit it
          const formAction =
            (data.extra.form_action as string) ||
            'https://rc-epay.esewa.com.np/api/epay/main/v2/form';
          submitHiddenForm(formAction, data.extra.form_fields as Record<string, unknown>);
        } else if (data.payment_url) {
          window.location.href = data.payment_url;
        } else {
          onSuccess?.();
        }
      },
      onError: (err) => onError?.(err as Error),
    });
  };

  const amountHint =
    selectedProvider === 'khalti'
      ? 'Amount in NPR — e.g. 10 sends 1000 paisa to Khalti'
      : selectedProvider === 'esewa'
        ? 'Amount in NPR — e.g. 100 = NPR 100'
        : '';

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Provider selection */}
      <div className="space-y-2">
        <Label>Payment Provider</Label>
        <div className="grid grid-cols-2 gap-2">
          {loadingProviders && (
            <p className="text-sm text-gray-500 col-span-2">Loading providers…</p>
          )}
          {providers?.map((provider) => (
            <button
              key={provider}
              type="button"
              onClick={() => setSelectedProvider(provider)}
              className={`p-3 rounded-lg border text-sm font-medium capitalize transition-colors ${
                selectedProvider === provider
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {provider}
            </button>
          ))}
        </div>
      </div>

      {/* Amount */}
      <div className="space-y-1">
        <Label htmlFor="pay-amount">Amount (NPR)</Label>
        <Input
          id="pay-amount"
          type="number"
          min="1"
          step="1"
          placeholder="e.g. 100"
          value={amountNpr}
          onChange={(e) => setAmountNpr(e.target.value)}
          required
        />
        {amountHint && <p className="text-xs text-gray-500">{amountHint}</p>}
      </div>

      {/* Order name */}
      <div className="space-y-1">
        <Label htmlFor="pay-order-name">Order / Product Name</Label>
        <Input
          id="pay-order-name"
          placeholder="e.g. Subscription Plan"
          value={orderName}
          onChange={(e) => setOrderName(e.target.value)}
          required
        />
      </div>

      {/* Order ID (auto-generated, read-only) */}
      <div className="space-y-1">
        <Label>Order ID (auto-generated)</Label>
        <Input value={orderId} readOnly className="bg-gray-50 text-gray-500 text-xs font-mono" />
      </div>

      {/* Optional customer info */}
      <details className="group">
        <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700 list-none flex items-center gap-1 select-none">
          <span className="transition-transform group-open:rotate-90 inline-block">▶</span>
          Customer info (optional)
        </summary>
        <div className="mt-3 space-y-3 pl-3 border-l border-gray-200">
          <div className="space-y-1">
            <Label htmlFor="cust-name">Name</Label>
            <Input
              id="cust-name"
              placeholder="Full name"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="cust-email">Email</Label>
            <Input
              id="cust-email"
              type="email"
              placeholder="email@example.com"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="cust-phone">Phone</Label>
            <Input
              id="cust-phone"
              placeholder="9800000000"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
            />
          </div>
        </div>
      </details>

      {/* Test credential hints */}
      {selectedProvider === 'khalti' && (
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 text-xs text-blue-800 space-y-0.5">
          <p className="font-semibold">Khalti Sandbox Credentials</p>
          <p>Mobile: 9800000000 – 9800000005</p>
          <p>MPIN: 1111 &nbsp;·&nbsp; OTP: 987654</p>
        </div>
      )}
      {selectedProvider === 'esewa' && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-xs text-green-800 space-y-0.5">
          <p className="font-semibold">eSewa Sandbox Credentials</p>
          <p>eSewa ID: 9806800001 – 9806800005</p>
          <p>Password: Nepal@123 &nbsp;·&nbsp; OTP: 123456</p>
        </div>
      )}

      <Button
        type="submit"
        className="w-full"
        isLoading={initiatePayment.isPending}
        disabled={!selectedProvider || !amountNpr || !orderName || initiatePayment.isPending}
      >
        <ExternalLink className="mr-2 h-4 w-4" />
        {initiatePayment.isPending ? 'Initiating…' : `Pay with ${selectedProvider || '…'}`}
      </Button>

      {initiatePayment.error && (
        <p className="text-sm text-red-600">
          {(initiatePayment.error as Error).message || 'Payment initiation failed. Please try again.'}
        </p>
      )}
    </form>
  );
}
