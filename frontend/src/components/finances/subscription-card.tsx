'use client';

import { useTransactions } from '@/hooks/use-finances';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { TransactionCard } from './payment-method-card';
import { CreditCard } from 'lucide-react';

export function TransactionListCard() {
  const { data, isLoading } = useTransactions();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Payment History
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {isLoading && <p className="text-sm text-gray-500">Loading transactions…</p>}
        {(data?.length ?? 0) === 0 && !isLoading && (
          <p className="text-sm text-gray-500">No transactions yet.</p>
        )}
        {data?.map((tx) => (
          <TransactionCard key={tx.id} transaction={tx} />
        ))}
      </CardContent>
    </Card>
  );
}
