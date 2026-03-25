// Multitenancy module types

export type TenantRole = 'owner' | 'admin' | 'member';
export type InvitationStatus = 'pending' | 'accepted' | 'expired' | 'revoked';

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  description: string;
  is_active: boolean;
  owner_id?: string;
  created_at: string;
  updated_at: string;
}

export interface TenantWithMembers extends Tenant {
  members: TenantMember[];
}

export interface TenantMember {
  id: string;
  tenant_id: string;
  user_id: string;
  role: TenantRole;
  is_active: boolean;
  joined_at: string;
}

export interface TenantInvitation {
  id: string;
  tenant_id: string;
  email: string;
  role: TenantRole;
  status: InvitationStatus;
  invited_by?: string;
  expires_at: string;
  created_at: string;
  accepted_at?: string;
}

export interface TenantCreate {
  name: string;
  slug: string;
  description?: string;
}

export interface TenantUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface TenantInvitationCreate {
  email: string;
  role?: TenantRole;
}
