// IAM / Auth module types

export interface User {
  id: string;
  username: string;
  email: string;
  created_at?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  is_confirmed: boolean;
  otp_enabled: boolean;
  otp_verified: boolean;
  first_name?: string;
  last_name?: string;
  phone?: string;
  image_url?: string;
  bio?: string;
  roles: string[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface SignupData {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  first_name?: string;
  last_name?: string;
}

export interface UserUpdate {
  email?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface ResetPasswordRequestData {
  email: string;
}

export interface ResetPasswordConfirmData {
  token: string;
  new_password: string;
  confirm_password: string;
}

export interface OTPLoginResponse {
  requires_otp: true;
  temp_token: string;
  message: string;
}

export interface VerifyOTPData {
  otp_code: string;
  temp_token: string;
}

export interface OTPSetupResponse {
  otp_base32: string;
  otp_auth_url: string;
  qr_code: string;
}
