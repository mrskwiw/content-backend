/**
 * User management types for admin functionality
 */

export interface SystemUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface UserStats {
  total: number;
  active: number;
  inactive: number;
  admins: number;
}

export interface CreateUserRequest {
  email: string;
  full_name: string;
  password: string;
  is_superuser?: boolean;
}
