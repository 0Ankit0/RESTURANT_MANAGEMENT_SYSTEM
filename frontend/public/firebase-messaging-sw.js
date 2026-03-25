self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.FCM_MSG?.data?.url || '/notifications';
  event.waitUntil(clients.openWindow(targetUrl));
});
