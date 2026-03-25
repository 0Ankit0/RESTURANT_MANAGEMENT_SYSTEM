'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useVerifyEmail, useResendVerification } from '@/hooks/use-auth';
import { MailCheck, XCircle, Loader2, RefreshCw } from 'lucide-react';

function VerifyEmailPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('t');
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'no-token'>('loading');
  const [message, setMessage] = useState('');
  const [resendSent, setResendSent] = useState(false);

  const verifyEmail = useVerifyEmail();
  const resend = useResendVerification();

  useEffect(() => {
    if (!token) {
      setStatus('no-token');
      return;
    }
    verifyEmail.mutate(token, {
      onSuccess: () => {
        setStatus('success');
        setMessage('Your email has been verified successfully!');
        setTimeout(() => router.push('/login'), 3000);
      },
      onError: () => {
        setStatus('error');
        setMessage('The verification link is invalid or has expired.');
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const handleResend = () => {
    resend.mutate(undefined, {
      onSuccess: () => setResendSent(true),
    });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Email Verification</h1>

        {status === 'loading' && (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
            <p className="text-gray-500">Verifying your email address…</p>
          </div>
        )}

        {status === 'success' && (
          <div className="space-y-4">
            <MailCheck className="h-14 w-14 text-green-500 mx-auto" />
            <p className="text-gray-700 font-medium">{message}</p>
            <p className="text-sm text-gray-400">Redirecting to login in a moment…</p>
          </div>
        )}

        {(status === 'error' || status === 'no-token') && (
          <div className="space-y-4">
            <XCircle className="h-14 w-14 text-red-500 mx-auto" />
            <p className="text-gray-700">
              {status === 'no-token'
                ? 'No verification token found. Please use the link from your email.'
                : message}
            </p>

            {resendSent ? (
              <p className="text-sm text-green-600 font-medium">
                ✓ Verification email sent! Please check your inbox.
              </p>
            ) : (
              <button
                onClick={handleResend}
                disabled={resend.isPending}
                className="flex items-center gap-2 mx-auto text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${resend.isPending ? 'animate-spin' : ''}`} />
                {resend.isPending ? 'Sending…' : 'Resend verification email'}
              </button>
            )}

            <Link href="/login" className="block text-sm text-gray-400 hover:underline">
              Back to login
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailPageInner />
    </Suspense>
  );
}
