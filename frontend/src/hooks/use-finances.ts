'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { analytics } from '@/lib/analytics';
import { PaymentEvents } from '@/lib/analytics/events';
import type {
  InitiatePaymentRequest,
  InitiatePaymentResponse,
  VerifyPaymentRequest,
  VerifyPaymentResponse,
  PaymentTransaction,
  PaymentProvider,
} from '@/types';

export function usePaymentProviders() {
  return useQuery({
    queryKey: ['payment-providers'],
    queryFn: async () => {
      const response = await apiClient.get<PaymentProvider[]>('/payments/providers/');
      return response.data;
    },
  });
}

export function useInitiatePayment() {
  return useMutation({
    mutationFn: async (data: InitiatePaymentRequest) => {
      const response = await apiClient.post<InitiatePaymentResponse>('/payments/initiate/', data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      analytics.capture(PaymentEvents.PAYMENT_INITIATED, {
        provider: variables.provider,
        amount: variables.amount,
        order_id: variables.purchase_order_id,
      });
    },
  });
}

export function useVerifyPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: VerifyPaymentRequest) => {
      const response = await apiClient.post<VerifyPaymentResponse>('/payments/verify/', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      analytics.capture(
        data.status === 'completed'
          ? PaymentEvents.PAYMENT_COMPLETED
          : data.status === 'failed'
            ? PaymentEvents.PAYMENT_FAILED
            : PaymentEvents.PAYMENT_INITIATED,
        { provider: data.provider, status: data.status },
      );
    },
  });
}

export function useReconcileTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (transactionId: string) => {
      const response = await apiClient.post<VerifyPaymentResponse>(`/payments/reconcile/${transactionId}/`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  });
}

export function useRetryTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (transactionId: string) => {
      const response = await apiClient.post<VerifyPaymentResponse>(`/payments/retry/${transactionId}/`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  });
}

export function useTransaction(transactionId: string) {
  return useQuery({
    queryKey: ['transactions', transactionId],
    queryFn: async () => {
      const response = await apiClient.get<PaymentTransaction>(`/payments/${transactionId}/`);
      return response.data;
    },
    enabled: Boolean(transactionId),
  });
}

/** Backend returns list (not paginated). Uses offset/limit params. */
export function useTransactions(params?: { limit?: number; offset?: number; provider?: string }) {
  return useQuery({
    queryKey: ['transactions', params],
    queryFn: async () => {
      const response = await apiClient.get<PaymentTransaction[]>('/payments/', { params });
      return response.data;
    },
  });
}
