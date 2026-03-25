// RBAC module types

export interface Role {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  description: string;
  created_at: string;
}

export interface RoleCreate {
  name: string;
  description?: string;
}

export interface PermissionCreate {
  resource: string;
  action: string;
  description?: string;
}

export interface RoleAssignment {
  user_id: string;
  role_id: string;
}

export interface PermissionAssignment {
  role_id: string;
  permission_id: string;
}

export interface UserRolesResponse {
  user_id: string;
  roles: Role[];
}

export interface RolePermissionsResponse {
  role_id: string;
  permissions: Permission[];
}

export interface CheckPermissionResponse {
  user_id: string;
  resource: string;
  action: string;
  allowed: boolean;
}
