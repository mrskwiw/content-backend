/**
 * Admin user management API client
 */
import apiClient from './client';
import type { SystemUser, UserStats, CreateUserRequest } from '@/types/user';

export const usersApi = {
  /**
   * List all users (admin only)
   */
  async list(skip = 0, limit = 100): Promise<SystemUser[]> {
    const { data } = await apiClient.get<SystemUser[]>('/api/admin/users', {
      params: { skip, limit },
    });
    return data;
  },

  /**
   * Get user statistics (admin only)
   */
  async getStats(): Promise<UserStats> {
    const { data } = await apiClient.get<UserStats>('/api/admin/users/stats');
    return data;
  },

  /**
   * List inactive users (admin only)
   */
  async listInactive(skip = 0, limit = 100): Promise<SystemUser[]> {
    const { data } = await apiClient.get<SystemUser[]>('/api/admin/users/inactive', {
      params: { skip, limit },
    });
    return data;
  },

  /**
   * Create a new user (admin only)
   */
  async create(input: CreateUserRequest): Promise<SystemUser> {
    const { data } = await apiClient.post<SystemUser>('/api/admin/users', {
      email: input.email,
      full_name: input.full_name,
      password: input.password,
      is_superuser: input.is_superuser ?? false,
    });
    return data;
  },

  /**
   * Activate a user (admin only)
   */
  async activate(userId: string): Promise<SystemUser> {
    const { data } = await apiClient.post<SystemUser>(`/api/admin/users/${userId}/activate`);
    return data;
  },

  /**
   * Deactivate a user (admin only)
   */
  async deactivate(userId: string): Promise<SystemUser> {
    const { data } = await apiClient.post<SystemUser>(`/api/admin/users/${userId}/deactivate`);
    return data;
  },

  /**
   * Promote user to admin (admin only)
   */
  async promote(userId: string): Promise<SystemUser> {
    const { data } = await apiClient.post<SystemUser>(`/api/admin/users/${userId}/promote`);
    return data;
  },

  /**
   * Demote user from admin (admin only)
   */
  async demote(userId: string): Promise<SystemUser> {
    const { data } = await apiClient.post<SystemUser>(`/api/admin/users/${userId}/demote`);
    return data;
  },
};
