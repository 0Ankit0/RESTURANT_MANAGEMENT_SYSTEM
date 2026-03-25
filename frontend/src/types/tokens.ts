// Token tracking module types

export type TokenType = 'access' | 'refresh' | 'password_reset' | 'email_verification' | 'temp_auth';

export interface TokenTracking {
  id: string;
  user_id: string;
  token_jti: string;
  token_type: TokenType;
  ip_address: string;
  user_agent: string;
  is_active: boolean;
  revoked_at?: string;
  revoke_reason: string;
  expires_at: string;
  created_at: string;
}
