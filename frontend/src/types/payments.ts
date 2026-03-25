// Finance / Payments module types

export type PaymentProvider = 'khalti' | 'esewa' | 'stripe' | 'paypal';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded' | 'cancelled';

export interface InitiatePaymentRequest {
  provider: PaymentProvider;
  amount: number;
  purchase_order_id: string;
  purchase_order_name: string;
  return_url: string;
  website_url?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
}

export interface InitiatePaymentResponse {
  transaction_id: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  payment_url?: string;
  provider_pidx?: string;
  extra?: Record<string, unknown>;
}

export interface VerifyPaymentRequest {
  provider: PaymentProvider;
  pidx?: string;       // Khalti
  oid?: string;        // eSewa legacy
  refId?: string;      // eSewa legacy
  data?: string;       // eSewa v2 base64-encoded callback data
  transaction_id?: string;
}

export interface VerifyPaymentResponse {
  transaction_id: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  amount?: number;
  provider_transaction_id?: string;
  extra?: Record<string, unknown>;
}

export interface PaymentTransaction {
  id: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  amount: number;
  currency: string;
  purchase_order_id: string;
  purchase_order_name: string;
  provider_transaction_id?: string;
  provider_pidx?: string;
  return_url: string;
  website_url: string;
  failure_reason?: string;
  created_at: string;
  updated_at: string;
}
