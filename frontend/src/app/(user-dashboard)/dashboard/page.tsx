'use client';

import { useAuthStore } from '@/store/auth-store';
import { useNotifications } from '@/hooks/use-notifications';
import { useTokens } from '@/hooks/use-tokens';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Bell, Shield, Key, AlertTriangle } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: notifData, isLoading: loadingNotifs } = useNotifications({ limit: 5 });
  const { data: tokenData } = useTokens({ limit: 1 });

  const recentNotifs = notifData?.items ?? [];
  const unreadCount = notifData?.unread_count ?? 0;
  const activeSessions = tokenData?.total ?? 0;

  const stats = [
    {
      name: 'Unread Notifications',
      value: String(unreadCount),
      icon: Bell,
      href: '/notifications',
      color: 'text-blue-600 bg-blue-50',
    },
    {
      name: 'Active Sessions',
      value: String(activeSessions),
      icon: Key,
      href: '/tokens',
      color: 'text-purple-600 bg-purple-50',
    },
    {
      name: '2FA Status',
      value: user?.otp_enabled ? 'Enabled' : 'Disabled',
      icon: Shield,
      href: '/profile',
      color: user?.otp_enabled ? 'text-green-600 bg-green-50' : 'text-yellow-600 bg-yellow-50',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">
          Welcome back{user?.first_name ? `, ${user.first_name}` : user?.username ? `, ${user.username}` : ''}!
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Link key={stat.name} href={stat.href}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">{stat.name}</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                  </div>
                  <div className={`h-12 w-12 rounded-lg flex items-center justify-center ${stat.color}`}>
                    <stat.icon className="h-6 w-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Recent Notifications
            </CardTitle>
            <Link href="/notifications" className="text-sm text-blue-600 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {loadingNotifs ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
                ))}
              </div>
            ) : recentNotifs.length === 0 ? (
              <div className="text-center py-8">
                <Bell className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No notifications yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentNotifs.map((n) => (
                  <div
                    key={n.id}
                    className={`flex items-start gap-3 p-3 rounded-lg ${n.is_read ? '' : 'bg-blue-50'}`}
                  >
                    <div
                      className={`mt-0.5 h-2 w-2 rounded-full flex-shrink-0 ${
                        n.is_read ? 'bg-gray-300' : 'bg-blue-500'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{n.title}</p>
                      <p className="text-xs text-gray-500 truncate">{n.body}</p>
                    </div>
                    <span className="text-xs text-gray-400 flex-shrink-0">
                      {new Date(n.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {[
                { href: '/profile', icon: Shield, label: 'Security Settings', desc: 'Manage 2FA & password', color: 'text-blue-600' },
                { href: '/tokens', icon: Key, label: 'Active Sessions', desc: 'View & revoke sessions', color: 'text-purple-600' },
                { href: '/notifications', icon: Bell, label: 'Notifications', desc: `${unreadCount} unread`, color: 'text-orange-600' },
              ].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex flex-col gap-2 p-4 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-colors"
                >
                  <item.icon className={`h-5 w-5 ${item.color}`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{item.label}</p>
                    <p className="text-xs text-gray-500">{item.desc}</p>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {!user?.is_confirmed && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-800">Email not verified</p>
                <p className="text-xs text-yellow-700 mt-1">
                  Please verify your email address to unlock all features.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!user?.otp_enabled && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-start gap-3">
                <Shield className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-orange-800">Two-factor authentication is disabled</p>
                  <p className="text-xs text-orange-700 mt-1">
                    Enable 2FA to add an extra layer of security to your account.
                  </p>
                </div>
              </div>
              <Link
                href="/profile"
                className="text-sm font-medium text-orange-700 hover:text-orange-900 underline flex-shrink-0"
              >
                Enable 2FA
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
