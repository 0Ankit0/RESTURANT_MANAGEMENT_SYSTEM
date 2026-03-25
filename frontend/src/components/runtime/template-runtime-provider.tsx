'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/auth-store';
import { useNotificationDevices, useNotificationPreferences, usePushConfig, useRegisterNotificationDevice, useSystemCapabilities } from '@/hooks';
import { registerCurrentPushDevice } from '@/lib/push-registration';

export function TemplateRuntimeProvider({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { data: capabilities } = useSystemCapabilities();
  const { data: pushConfig } = usePushConfig();
  const { data: preferences } = useNotificationPreferences({ enabled: isAuthenticated });
  const { data: devices } = useNotificationDevices({ enabled: isAuthenticated });
  const registerDevice = useRegisterNotificationDevice();

  const notificationsEnabled = capabilities?.modules.notifications ?? true;
  const activePushProvider = pushConfig?.provider;
  const shouldRegisterPush = Boolean(
    isAuthenticated &&
      notificationsEnabled &&
      preferences?.push_enabled &&
      activePushProvider
  );
  const hasMatchingDevice = Boolean(
    activePushProvider &&
      devices?.some((device) => device.provider === activePushProvider && device.is_active)
  );

  useEffect(() => {
    if (!shouldRegisterPush || !pushConfig || hasMatchingDevice || registerDevice.isPending) {
      return;
    }

    let cancelled = false;

    const syncDevice = async () => {
      const payload = await registerCurrentPushDevice(activePushProvider, pushConfig);

      if (!cancelled && payload) {
        registerDevice.mutate(payload);
      }
    };

    void syncDevice();

    return () => {
      cancelled = true;
    };
  }, [activePushProvider, hasMatchingDevice, pushConfig, registerDevice, shouldRegisterPush]);

  return <>{children}</>;
}
