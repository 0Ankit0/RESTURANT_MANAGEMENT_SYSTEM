'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useVerifyOTP } from '@/hooks/use-auth';

function OTPVerifyPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tempToken = searchParams.get('temp_token') || '';
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState('');

  const verifyOTP = useVerifyOTP();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    verifyOTP.mutate(
      { otp_code: otpCode, temp_token: tempToken },
      {
        onSuccess: () => {
          router.push('/dashboard');
        },
        onError: (err: unknown) => {
          const axiosErr = err as { response?: { data?: { detail?: string } } };
          setError(axiosErr?.response?.data?.detail || 'Invalid OTP code. Please try again.');
        },
      }
    );
  };

  if (!tempToken) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-700">Invalid session. Please log in again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Two-Factor Authentication</h1>
        <p className="text-gray-500 text-sm mb-6">
          Enter the 6-digit code from your authenticator app.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-1">
              OTP Code
            </label>
            <input
              id="otp"
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
              placeholder="000000"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-center text-xl tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={verifyOTP.isPending || otpCode.length !== 6}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {verifyOTP.isPending ? 'Verifying…' : 'Verify'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function OTPVerifyPage() {
  return (
    <Suspense>
      <OTPVerifyPageInner />
    </Suspense>
  );
}
