/**
 * User management types for admin functionality
 */

export interface SystemUser {
  id: string;
  email: string;
  fullName: string;
  isActive: boolean;
  isSuperuser: boolean;
  createdAt: string;
  updatedAt: string | null;
}

export interface UserStats {
  total: number;
  active: number;
  inactive: number;
  admins: number;
}

export interface CreateUserRequest {
  email: string;
  fullName: string;
  password: string;
  isSuperuser?: boolean;
}
