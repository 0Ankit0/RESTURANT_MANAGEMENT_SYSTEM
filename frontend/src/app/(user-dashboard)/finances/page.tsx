'use client';

import { useState } from 'react';
import { useTransactions } from '@/hooks/use-finances';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button, Skeleton } from '@/components/ui';
import { CreditCard, DollarSign, Plus } from 'lucide-react';
import { PaymentInitiateForm } from '@/components/finances/stripe-payment-form';
import type { PaymentTransaction } from '@/types';

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-gray-100 text-gray-700',
};

function TransactionRow({ tx }: { tx: PaymentTransaction }) {
  const color = STATUS_COLORS[tx.status] ?? 'bg-gray-100 text-gray-700';
  return (
    <tr className="border-b border-gray-100 last:border-0">
      <td className="py-3 text-sm text-gray-500">
        {new Date(tx.created_at).toLocaleDateString()}
      </td>
      <td className="py-3 text-sm text-gray-900 capitalize">{tx.provider}</td>
      <td className="py-3 text-sm font-medium text-gray-900">
        {tx.currency} {(tx.amount / 100).toFixed(2)}
      </td>
      <td className="py-3">
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
          {tx.status}
        </span>
      </td>
    </tr>
  );
}

export default function FinancesPage() {
  const [showPayForm, setShowPayForm] = useState(false);
  const { data: transactions, isLoading } = useTransactions();

  const txList = transactions ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
          <p className="text-gray-500">Initiate payments and view transaction history</p>
        </div>
        <Button onClick={() => setShowPayForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Payment
        </Button>
      </div>

      {showPayForm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Initiate Payment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <PaymentInitiateForm
              onSuccess={() => setShowPayForm(false)}
            />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Transaction History
            {txList.length > 0 && (
              <span className="ml-auto text-sm font-normal text-gray-500">{txList.length} records</span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : txList.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b border-gray-200">
                    <th className="pb-3 text-sm font-medium text-gray-500">Date</th>
                    <th className="pb-3 text-sm font-medium text-gray-500">Provider</th>
                    <th className="pb-3 text-sm font-medium text-gray-500">Amount</th>
                    <th className="pb-3 text-sm font-medium text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {txList.map((tx) => (
                    <TransactionRow key={tx.id} tx={tx} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <DollarSign className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No transactions yet</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
