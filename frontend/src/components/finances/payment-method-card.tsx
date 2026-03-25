'use client';

import { CreditCard } from 'lucide-react';
import type { PaymentTransaction } from '@/types';

interface TransactionCardProps {
  transaction: PaymentTransaction;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-purple-100 text-purple-800',
  cancelled: 'bg-gray-100 text-gray-600',
};

export function TransactionCard({ transaction }: TransactionCardProps) {
  return (
    <div className="p-4 rounded-lg border border-gray-200 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center">
          <CreditCard className="h-5 w-5 text-gray-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">{transaction.purchase_order_name}</p>
          <p className="text-sm text-gray-500 capitalize">{transaction.provider}</p>
        </div>
      </div>
      <div className="text-right">
        <p className="font-semibold text-gray-900">
          {(transaction.amount / 100).toFixed(2)} {transaction.currency.toUpperCase()}
        </p>
        <span
          className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${
            statusColors[transaction.status] ?? statusColors.pending
          }`}
        >
          {transaction.status}
        </span>
      </div>
    </div>
  );
}
