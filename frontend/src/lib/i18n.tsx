import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export type AppLanguage = 'en' | 'es' | 'fr';

const LANGUAGE_STORAGE_KEY = 'app-language';

const SUPPORTED_LANGUAGES: AppLanguage[] = ['en', 'es', 'fr'];

const MESSAGES: Record<AppLanguage, Record<string, string>> = {
  en: {
    'language.english': 'English',
    'language.spanish': 'Español',
    'language.french': 'Français',
    'header.organization': 'Organization',
    'header.notifications': 'Notifications',
    'header.markAllRead': 'Mark all read',
    'header.noNotifications': 'No notifications',
    'header.markRead': 'Mark read',
    'header.viewAllNotifications': 'View all notifications',
    'header.user': 'User',
    'header.profile': 'Profile',
    'header.settings': 'Settings',
    'header.signOut': 'Sign out',
    'header.signOutQuestion': 'Sign out?',
    'header.signOutDescription': 'You will be signed out of your account and redirected to the login page.',
    'common.cancel': 'Cancel',
    'org.personal': 'Personal',
    'org.account': 'Account',
    'org.organizations': 'Organizations',
    'org.addOrganization': 'Add organization',
    'sidebar.workspace': 'Workspace',
    'sidebar.dashboard': 'Dashboard',
    'sidebar.profile': 'Profile',
    'sidebar.tenants': 'Tenants',
    'sidebar.payments': 'Payments',
    'sidebar.notifications': 'Notifications',
    'sidebar.maps': 'Maps',
    'sidebar.restaurantOps': 'Restaurant Ops',
    'sidebar.activeSessions': 'Active Sessions',
    'sidebar.settings': 'Settings',
    'sidebar.openAdminPanel': 'Open Admin Panel',
    'admin.panel': 'Admin Panel',
    'admin.administration': 'Administration',
    'admin.adminDashboard': 'Admin Dashboard',
    'admin.logs': 'Logs',
    'admin.securityReview': 'Security Review',
    'admin.manageUsers': 'Manage Users',
    'admin.rolesPermissions': 'Roles & Permissions',
    'admin.backToWorkspace': 'Back to Workspace',
    'dashboard.welcomeBack': 'Welcome back, {name}!',
    'dashboard.unreadNotifications': 'Unread Notifications',
    'dashboard.activeSessions': 'Active Sessions',
    'dashboard.twoFactorStatus': '2FA Status',
    'dashboard.enabled': 'Enabled',
    'dashboard.disabled': 'Disabled',
    'dashboard.recentNotifications': 'Recent Notifications',
    'dashboard.viewAll': 'View all',
    'dashboard.noNotificationsYet': 'No notifications yet',
    'dashboard.quickActions': 'Quick Actions',
    'dashboard.securitySettings': 'Security Settings',
    'dashboard.manage2faPassword': 'Manage 2FA & password',
    'dashboard.viewRevokeSessions': 'View & revoke sessions',
    'dashboard.unreadCount': '{count} unread',
    'dashboard.emailNotVerified': 'Email not verified',
    'dashboard.verifyEmailPrompt': 'Please verify your email address to unlock all features.',
    'dashboard.twoFactorDisabled': 'Two-factor authentication is disabled',
    'dashboard.enable2faPrompt': 'Enable 2FA to add an extra layer of security to your account.',
    'dashboard.enable2fa': 'Enable 2FA',
    'adminDashboard.title': 'Admin Dashboard',
    'adminDashboard.overview': "Here's the current platform overview.",
    'adminDashboard.totalUsers': 'Total Users',
    'adminDashboard.rolesPermissions': 'Roles & Permissions',
    'adminDashboard.superusers': 'Superusers',
    'adminDashboard.openIncidents': 'Open Incidents',
    'adminDashboard.manageUsers': 'Manage Users',
    'adminDashboard.reviewAccounts': 'Review accounts and edit access',
    'adminDashboard.tuneRoles': 'Tune role and permission rules',
    'adminDashboard.liveLogs': 'Live Logs',
    'adminDashboard.watchEvents': 'Watch the persisted event stream',
    'adminDashboard.securityReview': 'Security Review',
    'adminDashboard.triageActivity': 'Triage suspicious activity',
    'adminDashboard.monitorTokens': 'Monitor and revoke tokens',
    'adminDashboard.userOverview': 'User Overview',
    'adminDashboard.activeUsers': 'Active users',
    'adminDashboard.accounts': '{count} accounts',
    'adminDashboard.superuserAccess': 'Superuser access',
    'adminDashboard.elevatedUsers': '{count} elevated users',
    'adminDashboard.unverifiedAccounts': 'Unverified accounts',
    'adminDashboard.pendingReview': '{count} pending review',
    'adminDashboard.accountsNeedAttention': 'Accounts need attention',
    'adminDashboard.needVerification': '{count} user account{suffix} still need email verification.',
    'adminDashboard.reviewUsers': 'Review users',
    'adminDashboard.operationsBlockers': 'Operations blockers',
    'adminDashboard.noActiveDayClose': 'No active day-close found for monitored branch.',
    'adminDashboard.severityCount': 'Severity: {severity} · Count: {count}',
    'adminDashboard.noBlockers': 'No unresolved operations blockers.',
  },
  es: {
    'language.english': 'Inglés',
    'language.spanish': 'Español',
    'language.french': 'Francés',
    'header.organization': 'Organización',
    'header.notifications': 'Notificaciones',
    'header.markAllRead': 'Marcar todo como leído',
    'header.noNotifications': 'Sin notificaciones',
    'header.markRead': 'Marcar leído',
    'header.viewAllNotifications': 'Ver todas las notificaciones',
    'header.user': 'Usuario',
    'header.profile': 'Perfil',
    'header.settings': 'Configuración',
    'header.signOut': 'Cerrar sesión',
    'header.signOutQuestion': '¿Cerrar sesión?',
    'header.signOutDescription': 'Se cerrará tu sesión y volverás a la página de inicio de sesión.',
    'common.cancel': 'Cancelar',
    'org.personal': 'Personal',
    'org.account': 'Cuenta',
    'org.organizations': 'Organizaciones',
    'org.addOrganization': 'Agregar organización',
    'sidebar.workspace': 'Espacio de trabajo',
    'sidebar.dashboard': 'Panel',
    'sidebar.profile': 'Perfil',
    'sidebar.tenants': 'Inquilinos',
    'sidebar.payments': 'Pagos',
    'sidebar.notifications': 'Notificaciones',
    'sidebar.maps': 'Mapas',
    'sidebar.restaurantOps': 'Operaciones del restaurante',
    'sidebar.activeSessions': 'Sesiones activas',
    'sidebar.settings': 'Configuración',
    'sidebar.openAdminPanel': 'Abrir panel de administración',
    'admin.panel': 'Panel de administración',
    'admin.administration': 'Administración',
    'admin.adminDashboard': 'Panel de administración',
    'admin.logs': 'Registros',
    'admin.securityReview': 'Revisión de seguridad',
    'admin.manageUsers': 'Gestionar usuarios',
    'admin.rolesPermissions': 'Roles y permisos',
    'admin.backToWorkspace': 'Volver al espacio de trabajo',
    'dashboard.welcomeBack': '¡Bienvenido de nuevo, {name}!',
    'dashboard.unreadNotifications': 'Notificaciones sin leer',
    'dashboard.activeSessions': 'Sesiones activas',
    'dashboard.twoFactorStatus': 'Estado de 2FA',
    'dashboard.enabled': 'Activado',
    'dashboard.disabled': 'Desactivado',
    'dashboard.recentNotifications': 'Notificaciones recientes',
    'dashboard.viewAll': 'Ver todo',
    'dashboard.noNotificationsYet': 'Aún no hay notificaciones',
    'dashboard.quickActions': 'Acciones rápidas',
    'dashboard.securitySettings': 'Configuración de seguridad',
    'dashboard.manage2faPassword': 'Gestiona 2FA y contraseña',
    'dashboard.viewRevokeSessions': 'Ver y revocar sesiones',
    'dashboard.unreadCount': '{count} sin leer',
    'dashboard.emailNotVerified': 'Correo no verificado',
    'dashboard.verifyEmailPrompt': 'Verifica tu correo para desbloquear todas las funciones.',
    'dashboard.twoFactorDisabled': 'La autenticación de dos factores está desactivada',
    'dashboard.enable2faPrompt': 'Activa 2FA para añadir una capa extra de seguridad a tu cuenta.',
    'dashboard.enable2fa': 'Activar 2FA',
    'adminDashboard.title': 'Panel de administración',
    'adminDashboard.overview': 'Este es el resumen actual de la plataforma.',
    'adminDashboard.totalUsers': 'Usuarios totales',
    'adminDashboard.rolesPermissions': 'Roles y permisos',
    'adminDashboard.superusers': 'Superusuarios',
    'adminDashboard.openIncidents': 'Incidentes abiertos',
    'adminDashboard.manageUsers': 'Gestionar usuarios',
    'adminDashboard.reviewAccounts': 'Revisa cuentas y edita accesos',
    'adminDashboard.tuneRoles': 'Ajusta reglas de roles y permisos',
    'adminDashboard.liveLogs': 'Registros en vivo',
    'adminDashboard.watchEvents': 'Supervisa el flujo de eventos persistido',
    'adminDashboard.securityReview': 'Revisión de seguridad',
    'adminDashboard.triageActivity': 'Clasifica actividad sospechosa',
    'adminDashboard.monitorTokens': 'Monitorea y revoca tokens',
    'adminDashboard.userOverview': 'Resumen de usuarios',
    'adminDashboard.activeUsers': 'Usuarios activos',
    'adminDashboard.accounts': '{count} cuentas',
    'adminDashboard.superuserAccess': 'Acceso de superusuario',
    'adminDashboard.elevatedUsers': '{count} usuarios elevados',
    'adminDashboard.unverifiedAccounts': 'Cuentas sin verificar',
    'adminDashboard.pendingReview': '{count} pendientes de revisión',
    'adminDashboard.accountsNeedAttention': 'Cuentas que requieren atención',
    'adminDashboard.needVerification': '{count} cuenta{suffix} aún requieren verificación de correo.',
    'adminDashboard.reviewUsers': 'Revisar usuarios',
    'adminDashboard.operationsBlockers': 'Bloqueos operativos',
    'adminDashboard.noActiveDayClose': 'No se encontró un cierre de día activo para la sucursal monitoreada.',
    'adminDashboard.severityCount': 'Severidad: {severity} · Cantidad: {count}',
    'adminDashboard.noBlockers': 'No hay bloqueos operativos sin resolver.',
  },
  fr: {
    'language.english': 'Anglais',
    'language.spanish': 'Espagnol',
    'language.french': 'Français',
    'header.organization': 'Organisation',
    'header.notifications': 'Notifications',
    'header.markAllRead': 'Tout marquer comme lu',
    'header.noNotifications': 'Aucune notification',
    'header.markRead': 'Marquer comme lu',
    'header.viewAllNotifications': 'Voir toutes les notifications',
    'header.user': 'Utilisateur',
    'header.profile': 'Profil',
    'header.settings': 'Paramètres',
    'header.signOut': 'Se déconnecter',
    'header.signOutQuestion': 'Se déconnecter ?',
    'header.signOutDescription': 'Vous serez déconnecté de votre compte et redirigé vers la page de connexion.',
    'common.cancel': 'Annuler',
    'org.personal': 'Personnel',
    'org.account': 'Compte',
    'org.organizations': 'Organisations',
    'org.addOrganization': 'Ajouter une organisation',
    'sidebar.workspace': 'Espace de travail',
    'sidebar.dashboard': 'Tableau de bord',
    'sidebar.profile': 'Profil',
    'sidebar.tenants': 'Locataires',
    'sidebar.payments': 'Paiements',
    'sidebar.notifications': 'Notifications',
    'sidebar.maps': 'Cartes',
    'sidebar.restaurantOps': 'Opérations du restaurant',
    'sidebar.activeSessions': 'Sessions actives',
    'sidebar.settings': 'Paramètres',
    'sidebar.openAdminPanel': "Ouvrir le panneau d'administration",
    'admin.panel': "Panneau d'administration",
    'admin.administration': 'Administration',
    'admin.adminDashboard': "Tableau de bord d'administration",
    'admin.logs': 'Journaux',
    'admin.securityReview': 'Revue de sécurité',
    'admin.manageUsers': 'Gérer les utilisateurs',
    'admin.rolesPermissions': 'Rôles et permissions',
    'admin.backToWorkspace': "Retour à l'espace de travail",
    'dashboard.welcomeBack': 'Bon retour, {name} !',
    'dashboard.unreadNotifications': 'Notifications non lues',
    'dashboard.activeSessions': 'Sessions actives',
    'dashboard.twoFactorStatus': 'Statut 2FA',
    'dashboard.enabled': 'Activé',
    'dashboard.disabled': 'Désactivé',
    'dashboard.recentNotifications': 'Notifications récentes',
    'dashboard.viewAll': 'Tout voir',
    'dashboard.noNotificationsYet': 'Aucune notification pour le moment',
    'dashboard.quickActions': 'Actions rapides',
    'dashboard.securitySettings': 'Paramètres de sécurité',
    'dashboard.manage2faPassword': 'Gérer 2FA et mot de passe',
    'dashboard.viewRevokeSessions': 'Voir et révoquer les sessions',
    'dashboard.unreadCount': '{count} non lues',
    'dashboard.emailNotVerified': 'E-mail non vérifié',
    'dashboard.verifyEmailPrompt': 'Veuillez vérifier votre e-mail pour débloquer toutes les fonctionnalités.',
    'dashboard.twoFactorDisabled': "L'authentification à deux facteurs est désactivée",
    'dashboard.enable2faPrompt': 'Activez la 2FA pour ajouter une couche de sécurité supplémentaire à votre compte.',
    'dashboard.enable2fa': 'Activer la 2FA',
    'adminDashboard.title': "Tableau de bord d'administration",
    'adminDashboard.overview': 'Voici un aperçu actuel de la plateforme.',
    'adminDashboard.totalUsers': 'Utilisateurs totaux',
    'adminDashboard.rolesPermissions': 'Rôles et permissions',
    'adminDashboard.superusers': 'Super-utilisateurs',
    'adminDashboard.openIncidents': 'Incidents ouverts',
    'adminDashboard.manageUsers': 'Gérer les utilisateurs',
    'adminDashboard.reviewAccounts': 'Examiner les comptes et modifier les accès',
    'adminDashboard.tuneRoles': 'Ajuster les règles des rôles et permissions',
    'adminDashboard.liveLogs': 'Journaux en direct',
    'adminDashboard.watchEvents': "Surveiller le flux d'événements persisté",
    'adminDashboard.securityReview': 'Revue de sécurité',
    'adminDashboard.triageActivity': 'Trier les activités suspectes',
    'adminDashboard.monitorTokens': 'Surveiller et révoquer les jetons',
    'adminDashboard.userOverview': 'Aperçu des utilisateurs',
    'adminDashboard.activeUsers': 'Utilisateurs actifs',
    'adminDashboard.accounts': '{count} comptes',
    'adminDashboard.superuserAccess': 'Accès super-utilisateur',
    'adminDashboard.elevatedUsers': '{count} utilisateurs élevés',
    'adminDashboard.unverifiedAccounts': 'Comptes non vérifiés',
    'adminDashboard.pendingReview': '{count} en attente de revue',
    'adminDashboard.accountsNeedAttention': 'Comptes nécessitant une attention',
    'adminDashboard.needVerification': '{count} compte{suffix} nécessitent encore une vérification e-mail.',
    'adminDashboard.reviewUsers': 'Examiner les utilisateurs',
    'adminDashboard.operationsBlockers': 'Blocages opérationnels',
    'adminDashboard.noActiveDayClose': 'Aucune clôture de journée active trouvée pour la succursale surveillée.',
    'adminDashboard.severityCount': 'Sévérité : {severity} · Nombre : {count}',
    'adminDashboard.noBlockers': 'Aucun blocage opérationnel non résolu.',
  },
};

function isLanguage(value: string | null): value is AppLanguage {
  return !!value && SUPPORTED_LANGUAGES.includes(value as AppLanguage);
}

function format(template: string, values?: Record<string, string | number>) {
  if (!values) {
    return template;
  }

  return template.replace(/\{(\w+)\}/g, (_, key: string) => {
    const value = values[key];
    return value === undefined ? '' : String(value);
  });
}

type I18nContextValue = {
  language: AppLanguage;
  setLanguage: (language: AppLanguage) => void;
  t: (key: string, values?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

function detectLanguage(): AppLanguage {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
  if (isLanguage(stored)) {
    return stored;
  }

  const browserCode = navigator.language.slice(0, 2);
  if (isLanguage(browserCode)) {
    return browserCode;
  }

  return 'en';
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<AppLanguage>(() => detectLanguage());

  useEffect(() => {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

  const t = useCallback(
    (key: string, values?: Record<string, string | number>) => {
      const localeMessage = MESSAGES[language][key] ?? MESSAGES.en[key] ?? key;
      return format(localeMessage, values);
    },
    [language]
  );

  const contextValue = useMemo(
    () => ({
      language,
      setLanguage,
      t,
    }),
    [language, t]
  );

  return <I18nContext.Provider value={contextValue}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }

  return context;
}
