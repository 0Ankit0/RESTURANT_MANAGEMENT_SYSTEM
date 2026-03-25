'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAcceptInvitation } from '@/hooks/use-tenants';
import { useAuthStore } from '@/store/auth-store';

function AcceptInvitationPageInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');
  const { isAuthenticated } = useAuthStore();
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const acceptInvitation = useAcceptInvitation();

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('No invitation token found in the URL.');
      return;
    }

    if (!isAuthenticated) {
      router.push(`/login?redirect=/accept-invitation?token=${token}`);
      return;
    }

    setStatus('loading');
    acceptInvitation.mutate(token, {
      onSuccess: () => {
        setStatus('success');
        setMessage('You have successfully joined the team!');
        setTimeout(() => router.push('/tenants'), 2000);
      },
      onError: (err: unknown) => {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setStatus('error');
        setMessage(axiosErr?.response?.data?.detail || 'Failed to accept invitation.');
      },
    });
  }, [acceptInvitation, isAuthenticated, router, token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Team Invitation</h1>

        {status === 'loading' && <p className="text-gray-500">Accepting your invitation…</p>}

        {status === 'success' && (
          <>
            <div className="mb-4 text-green-600 text-4xl">✓</div>
            <p className="text-gray-700">{message}</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="mb-4 text-red-500 text-4xl">✗</div>
            <p className="text-gray-700">{message}</p>
          </>
        )}
      </div>
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense>
      <AcceptInvitationPageInner />
    </Suspense>
  );
}
