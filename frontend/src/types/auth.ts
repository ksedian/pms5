export interface User {
  id: number;
  username: string;
  email: string;
  roles: string[];
  permissions: string[];
  is_2fa_enabled: boolean;
  is_active: boolean;
  phone_number?: string;
  last_login?: string;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  is_system_role: boolean;
  permissions: string[];
  user_count: number;
}

export interface Permission {
  id: number;
  name: string;
  description: string;
  resource: string;
  action: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
  requires_2fa?: boolean;
  user_id?: number;
}

export interface TwoFactorSetupResponse {
  qr_code: string;
  backup_codes: string[];
  secret: string;
}

export interface AuditLog {
  id: number;
  user_id: number;
  username: string;
  event_type: string;
  event_description: string;
  ip_address: string;
  user_agent: string;
  success: boolean;
  timestamp: string;
  metadata?: any;
}

export interface ApiResponse<T = any> {
  message: string;
  data?: T;
}

export interface UserProfileResponse {
  user: User;
}

export interface ApiError {
  message: string;
  errors?: string[];
} 