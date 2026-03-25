'use client';

import { useMarkNotificationRead } from '@/hooks/use-notifications';
import { Bell, Info, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import type { Notification } from '@/types';

interface NotificationItemProps {
  notification: Notification;
  onClick?: () => void;
}

const typeIcons: Record<string, typeof Bell> = {
  info: Info,
  success: CheckCircle,
  warning: AlertCircle,
  error: XCircle,
  default: Bell,
};

const typeColors: Record<string, string> = {
  info: 'bg-blue-100 text-blue-600',
  success: 'bg-green-100 text-green-600',
  warning: 'bg-yellow-100 text-yellow-600',
  error: 'bg-red-100 text-red-600',
  default: 'bg-gray-100 text-gray-600',
};

function formatTime(dateString: string) {
  const date = new Date(dateString);
  const diff = Date.now() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString();
}

export function NotificationItem({ notification, onClick }: NotificationItemProps) {
  const markRead = useMarkNotificationRead();

  const Icon = typeIcons[notification.type] ?? typeIcons.default;
  const colorClass = typeColors[notification.type] ?? typeColors.default;

  const handleClick = () => {
    if (!notification.is_read) markRead.mutate(notification.id);
    onClick?.();
  };

  return (
    <div
      onClick={handleClick}
      className={`flex items-start gap-3 p-4 cursor-pointer transition-colors ${
        notification.is_read ? 'bg-white hover:bg-gray-50' : 'bg-blue-50 hover:bg-blue-100'
      }`}
    >
      <div className={`flex-shrink-0 h-10 w-10 rounded-full flex items-center justify-center ${colorClass}`}>
        <Icon className="h-5 w-5" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={`text-sm ${notification.is_read ? 'text-gray-700' : 'text-gray-900 font-medium'}`}>
            {notification.title}
          </p>
          <span className="text-xs text-gray-400 whitespace-nowrap">
            {formatTime(notification.created_at)}
          </span>
        </div>
        {notification.body && (
          <p className="text-sm text-gray-500 mt-0.5 truncate">{notification.body}</p>
        )}
      </div>

      {!notification.is_read && (
        <div className="flex-shrink-0 mt-1">
          <div className="h-2 w-2 rounded-full bg-blue-600" />
        </div>
      )}
    </div>
  );
}
