'use client';

import { useState } from 'react';
import { useNotifications, useMarkAllNotificationsRead } from '@/hooks/use-notifications';
import { useNotificationWebSocket } from '@/hooks/use-websocket';
import { Bell, CheckCheck, X } from 'lucide-react';
import { NotificationItem } from './notification-item';
import { Button } from '@/components/ui/button';

interface NotificationBellProps {
  onViewAll?: () => void;
}

export function NotificationBell({ onViewAll }: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { data: notifData } = useNotifications({ limit: 5 });
  const markAllRead = useMarkAllNotificationsRead();

  useNotificationWebSocket();

  const recentNotifications = notifData?.items ?? [];
  const unreadCount = notifData?.unread_count ?? 0;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center bg-red-500 text-white text-xs font-medium rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-20">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={() => markAllRead.mutate()}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                  >
                    <CheckCheck className="h-4 w-4" />
                    Mark all read
                  </button>
                )}
                <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-gray-100 rounded">
                  <X className="h-4 w-4 text-gray-400" />
                </button>
              </div>
            </div>

            <div className="max-h-96 overflow-y-auto divide-y divide-gray-100">
              {recentNotifications.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 text-sm">No notifications yet</p>
                </div>
              ) : (
                recentNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClick={() => setIsOpen(false)}
                  />
                ))
              )}
            </div>

            {recentNotifications.length > 0 && onViewAll && (
              <div className="p-3 border-t border-gray-200">
                <Button
                  variant="ghost"
                  className="w-full"
                  onClick={() => {
                    setIsOpen(false);
                    onViewAll();
                  }}
                >
                  View All Notifications
                </Button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
