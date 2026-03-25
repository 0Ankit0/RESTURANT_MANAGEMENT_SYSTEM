'use client';

import { useTokens, useRevokeToken, useRevokeAllTokens } from '@/hooks/use-tokens';

export default function TokensPage() {
  const tokensQuery = useTokens();
  const revokeToken = useRevokeToken();
  const revokeAll = useRevokeAllTokens();

  const activeTokens = tokensQuery.data?.items.filter((t) => t.is_active) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Active Sessions</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your active login sessions and tokens.</p>
        </div>
        <button
          onClick={() => revokeAll.mutate()}
          disabled={revokeAll.isPending || activeTokens.length === 0}
          className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
        >
          {revokeAll.isPending ? 'Revoking…' : 'Revoke All'}
        </button>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {tokensQuery.isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-4 text-center text-gray-500">Loading…</td>
              </tr>
            )}
            {tokensQuery.data?.items.map((token) => (
              <tr key={token.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                    token.token_type === 'access'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-purple-100 text-purple-800'
                  }`}>
                    {token.token_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700 font-mono">{token.ip_address}</td>
                <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate" title={token.user_agent}>
                  {token.user_agent}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">
                  {new Date(token.expires_at).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                    token.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {token.is_active ? 'Active' : 'Revoked'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {token.is_active && (
                    <button
                      onClick={() => revokeToken.mutate(token.id)}
                      disabled={revokeToken.isPending}
                      className="text-sm text-red-600 hover:underline disabled:opacity-50"
                    >
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {tokensQuery.data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-4 text-center text-gray-500">No tokens found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
