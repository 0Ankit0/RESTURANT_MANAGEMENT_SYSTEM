'use client';

import { Suspense } from 'react';
import { ResetPasswordForm } from '@/components/auth/reset-password-form';

function ResetPasswordContent() {
  return <ResetPasswordForm />;
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="animate-pulse">Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
