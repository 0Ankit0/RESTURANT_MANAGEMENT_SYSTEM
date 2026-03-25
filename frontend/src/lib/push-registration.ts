'use client';

import type { NotificationDeviceCreate, PushConfigResponse } from '@/types';

declare global {
  interface Window {
    OneSignalDeferred?: Array<(OneSignal: any) => void>;
  }
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

async function loadScript(src: string): Promise<void> {
  if (document.querySelector(`script[src="${src}"]`)) {
    return;
  }
  await new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
    document.head.appendChild(script);
  });
}

export async function registerWebPush(
  pushConfig: PushConfigResponse
): Promise<NotificationDeviceCreate | null> {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    return null;
  }

  const config = pushConfig.providers.webpush;
  if (!config.enabled || !config.vapid_public_key) {
    return null;
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    return null;
  }

  const registration = await navigator.serviceWorker.register('/sw.js');
  const existing = await registration.pushManager.getSubscription();
  const subscription =
    existing ??
    (await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(config.vapid_public_key) as BufferSource,
    }));
  const subscriptionJson = subscription.toJSON();

  return {
    provider: 'webpush',
    platform: 'web',
    endpoint: subscription.endpoint,
    p256dh: subscriptionJson.keys?.p256dh,
    auth: subscriptionJson.keys?.auth,
    device_metadata: { userAgent: navigator.userAgent },
  };
}

export async function registerFcm(
  pushConfig: PushConfigResponse
): Promise<NotificationDeviceCreate | null> {
  const config = pushConfig.providers.fcm;
  if (!config.enabled || !config.api_key || !config.app_id || !config.messaging_sender_id) {
    return null;
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    return null;
  }

  const [{ getApps, initializeApp }, messagingModule] = await Promise.all([
    import('firebase/app'),
    import('firebase/messaging'),
  ]);

  if (!(await messagingModule.isSupported())) {
    return null;
  }

  const existingApp = getApps().find((app: { name: string }) => app.name === 'template-push');
  const app =
    existingApp ??
    initializeApp(
      {
        apiKey: config.api_key,
        appId: config.app_id,
        authDomain: config.auth_domain,
        measurementId: config.measurement_id,
        messagingSenderId: config.messaging_sender_id,
        projectId: config.project_id,
        storageBucket: config.storage_bucket,
      },
      'template-push'
    );
  const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
  const messaging = messagingModule.getMessaging(app);
  const token = await messagingModule.getToken(messaging, {
    vapidKey: config.web_vapid_key,
    serviceWorkerRegistration: registration,
  });

  if (!token) {
    return null;
  }

  return {
    provider: 'fcm',
    platform: 'web',
    token,
    device_metadata: { userAgent: navigator.userAgent },
  };
}

export async function registerOneSignal(
  pushConfig: PushConfigResponse
): Promise<NotificationDeviceCreate | null> {
  const config = pushConfig.providers.onesignal;
  if (!config.enabled || !config.app_id) {
    return null;
  }

  await loadScript('https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js');
  window.OneSignalDeferred = window.OneSignalDeferred || [];

  return new Promise<NotificationDeviceCreate | null>((resolve) => {
    window.OneSignalDeferred?.push(async (OneSignal) => {
      try {
        await OneSignal.init({
          appId: config.app_id,
          allowLocalhostAsSecureOrigin: true,
        });
        await OneSignal.Notifications.requestPermission();
        const subscriptionId = OneSignal.User?.PushSubscription?.id;
        if (!subscriptionId) {
          resolve(null);
          return;
        }
        resolve({
          provider: 'onesignal',
          platform: 'web',
          subscription_id: subscriptionId,
          device_metadata: { userAgent: navigator.userAgent },
        });
      } catch {
        resolve(null);
      }
    });
  });
}

export async function registerCurrentPushDevice(
  activeProvider: string | null | undefined,
  pushConfig: PushConfigResponse
): Promise<NotificationDeviceCreate | null> {
  if (activeProvider === 'webpush') {
    return registerWebPush(pushConfig);
  }
  if (activeProvider === 'fcm') {
    return registerFcm(pushConfig);
  }
  if (activeProvider === 'onesignal') {
    return registerOneSignal(pushConfig);
  }
  return null;
}
