const preloadRoutes = [
  () => import('@/app/(auth)/login/page'),
  () => import('@/app/(auth)/signup/page'),
  () => import('@/app/(user-dashboard)/layout'),
  () => import('@/app/(user-dashboard)/dashboard/page'),
  () => import('@/app/(user-dashboard)/notifications/page'),
  () => import('@/app/(user-dashboard)/profile/page'),
  () => import('@/app/(admin-dashboard)/layout'),
  () => import('@/app/(admin-dashboard)/admin/dashboard/page'),
] as const;

export function preloadCriticalRoutes() {
  preloadRoutes.forEach((loader) => {
    void loader();
  });
}
