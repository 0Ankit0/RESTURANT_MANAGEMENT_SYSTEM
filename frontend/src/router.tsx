import { lazy, Suspense, type ComponentType } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';

const RootPage = lazy(() => import('@/app/page'));

const AuthLayout = lazy(() => import('@/app/(auth)/layout'));
const LoginPage = lazy(() => import('@/app/(auth)/login/page'));
const SignupPage = lazy(() => import('@/app/(auth)/signup/page'));
const ForgotPasswordPage = lazy(() => import('@/app/(auth)/forgot-password/page'));
const ResetPasswordPage = lazy(() => import('@/app/(auth)/reset-password/page'));
const OtpVerifyPage = lazy(() => import('@/app/(auth)/otp-verify/page'));
const AcceptInvitationPage = lazy(() => import('@/app/(auth)/accept-invitation/page'));
const AuthCallbackPage = lazy(() => import('@/app/(auth)/auth-callback/page'));
const PaymentCallbackPage = lazy(() => import('@/app/(auth)/payment-callback/page'));
const VerifyEmailPage = lazy(() => import('@/app/(auth)/verify-email/page'));

const UserDashboardLayout = lazy(() => import('@/app/(user-dashboard)/layout'));
const DashboardPage = lazy(() => import('@/app/(user-dashboard)/dashboard/page'));
const RestaurantPage = lazy(() => import('@/app/(user-dashboard)/restaurant/page'));
const TenantsPage = lazy(() => import('@/app/(user-dashboard)/tenants/page'));
const MapsPage = lazy(() => import('@/app/(user-dashboard)/maps/page'));
const TokensPage = lazy(() => import('@/app/(user-dashboard)/tokens/page'));
const FinancesPage = lazy(() => import('@/app/(user-dashboard)/finances/page'));
const NotificationsPage = lazy(() => import('@/app/(user-dashboard)/notifications/page'));
const UserRbacPage = lazy(() => import('@/app/(user-dashboard)/rbac/page'));
const UserRoleManagePage = lazy(() => import('@/app/(user-dashboard)/rbac/[roleId]/page'));
const SettingsPage = lazy(() => import('@/app/(user-dashboard)/settings/page'));
const ProfilePage = lazy(() => import('@/app/(user-dashboard)/profile/page'));

const AdminDashboardLayout = lazy(() => import('@/app/(admin-dashboard)/layout'));
const AdminDashboardPage = lazy(() => import('@/app/(admin-dashboard)/admin/dashboard/page'));
const AdminRbacPage = lazy(() => import('@/app/(admin-dashboard)/admin/rbac/page'));
const AdminRoleManagePage = lazy(() => import('@/app/(admin-dashboard)/admin/rbac/[roleId]/page'));
const AdminSecurityReviewPage = lazy(() => import('@/app/(admin-dashboard)/admin/security-review/page'));
const AdminUsersPage = lazy(() => import('@/app/(admin-dashboard)/admin/users/page'));

function RouteFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  );
}

function routeElement(Page: ComponentType) {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Page />
    </Suspense>
  );
}

function withLayout(
  Layout: ComponentType<{ children: React.ReactNode }>,
  Page: ComponentType
) {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Layout>
        <Page />
      </Layout>
    </Suspense>
  );
}

export const appRouter = createBrowserRouter([
  { path: '/', element: routeElement(RootPage) },

  { path: '/login', element: withLayout(AuthLayout, LoginPage) },
  { path: '/signup', element: withLayout(AuthLayout, SignupPage) },
  { path: '/forgot-password', element: withLayout(AuthLayout, ForgotPasswordPage) },
  { path: '/reset-password', element: withLayout(AuthLayout, ResetPasswordPage) },
  { path: '/otp-verify', element: withLayout(AuthLayout, OtpVerifyPage) },
  { path: '/accept-invitation', element: withLayout(AuthLayout, AcceptInvitationPage) },
  { path: '/auth-callback', element: withLayout(AuthLayout, AuthCallbackPage) },
  { path: '/payment-callback', element: withLayout(AuthLayout, PaymentCallbackPage) },
  { path: '/verify-email', element: withLayout(AuthLayout, VerifyEmailPage) },

  { path: '/dashboard', element: withLayout(UserDashboardLayout, DashboardPage) },
  { path: '/restaurant', element: withLayout(UserDashboardLayout, RestaurantPage) },
  { path: '/tenants', element: withLayout(UserDashboardLayout, TenantsPage) },
  { path: '/maps', element: withLayout(UserDashboardLayout, MapsPage) },
  { path: '/tokens', element: withLayout(UserDashboardLayout, TokensPage) },
  { path: '/finances', element: withLayout(UserDashboardLayout, FinancesPage) },
  { path: '/notifications', element: withLayout(UserDashboardLayout, NotificationsPage) },
  { path: '/rbac', element: withLayout(UserDashboardLayout, UserRbacPage) },
  { path: '/rbac/:roleId', element: withLayout(UserDashboardLayout, UserRoleManagePage) },
  { path: '/settings', element: withLayout(UserDashboardLayout, SettingsPage) },
  { path: '/profile', element: withLayout(UserDashboardLayout, ProfilePage) },

  { path: '/admin/dashboard', element: withLayout(AdminDashboardLayout, AdminDashboardPage) },
  { path: '/admin/rbac', element: withLayout(AdminDashboardLayout, AdminRbacPage) },
  { path: '/admin/rbac/:roleId', element: withLayout(AdminDashboardLayout, AdminRoleManagePage) },
  {
    path: '/admin/security-review',
    element: withLayout(AdminDashboardLayout, AdminSecurityReviewPage),
  },
  { path: '/admin/users', element: withLayout(AdminDashboardLayout, AdminUsersPage) },

  { path: '*', element: <Navigate to="/" replace /> },
]);
