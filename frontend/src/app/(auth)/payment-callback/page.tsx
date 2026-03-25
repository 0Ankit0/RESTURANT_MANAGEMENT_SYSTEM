'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useVerifyPayment } from '@/hooks/use-finances';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import Link from 'next/link';
import type { PaymentProvider } from '@/types';

/**
 * Handles payment provider callbacks.
 *
 * Khalti redirect params: ?status=Completed&transaction_id=...&tidx=...&amount=...&mobile=...&purchase_order_id=...&purchase_order_name=...&pidx=...
 * eSewa redirect params:  ?data=BASE64_ENCODED_RESPONSE&provider=esewa
 * Generic:                ?provider=stripe|paypal&transaction_id=...
 */
function PaymentCallbackInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  const verifyPayment = useVerifyPayment();

  useEffect(() => {
    const provider = (searchParams.get('provider') || 'khalti') as PaymentProvider;
    const pidx = searchParams.get('pidx') ?? undefined;
    const data = searchParams.get('data') ?? undefined;

    if (!pidx && !data) {
      setStatus('error');
      setMessage('Missing payment verification data in URL.');
      return;
    }

    verifyPayment.mutate(
      { provider, pidx, data },
      {
        onSuccess: (result) => {
          if (result.status === 'completed') {
            setStatus('success');
            setMessage(`Payment of ${result.amount ? result.amount / 100 : ''} completed successfully.`);
            setTimeout(() => router.push('/finances'), 4000);
          } else {
            setStatus('error');
            setMessage(`Payment status: ${result.status}. Please try again or contact support.`);
          }
        },
        onError: () => {
          setStatus('error');
          setMessage('Payment verification failed. Please check your transactions or contact support.');
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Payment Verification</h1>

        {status === 'loading' && (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
            <p className="text-gray-500">Verifying your payment…</p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4">
            <CheckCircle className="h-14 w-14 text-green-500 mx-auto" />
            <p className="text-gray-700 font-medium">{message}</p>
            <p className="text-sm text-gray-400">Redirecting to payments…</p>
            <Link href="/finances" className="text-sm text-blue-600 hover:underline">
              Go to Payments
            </Link>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4">
            <XCircle className="h-14 w-14 text-red-500 mx-auto" />
            <p className="text-gray-700">{message}</p>
            <div className="flex flex-col gap-2">
              <Link href="/finances" className="text-sm text-blue-600 hover:underline">
                View Payments
              </Link>
              <Link href="/dashboard" className="text-sm text-gray-400 hover:underline">
                Go to Dashboard
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function PaymentCallbackPage() {
  return (
    <Suspense>
      <PaymentCallbackInner />
    </Suspense>
  );
}
