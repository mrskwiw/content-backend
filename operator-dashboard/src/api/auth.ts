import apiClient from './client';
import type { LoginRequest, LoginResponse, RefreshTokenResponse } from '@/types/api';

// Backend response type (matches backend UserResponse schema)
interface BackendLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at: string;
    updated_at?: string;
  };
}

export const authApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const { data, status, headers } = await apiClient.post<BackendLoginResponse>('/api/auth/login', credentials);

    const contentType = headers['content-type'] || headers['Content-Type'] || '';
    const hasTokens =
      typeof data?.access_token === 'string' &&
      typeof data?.refresh_token === 'string' &&
      typeof data?.user === 'object';

    if (!hasTokens) {
      const snippet = JSON.stringify(data ?? {}, null, 0).slice(0, 120);
      throw new Error(
        `Login failed: unexpected response (status ${status}, content-type ${contentType}). Payload preview: ${snippet}`
      );
    }

    // Map backend user model to frontend User type
    const backendUser = data.user;
    const user: LoginResponse['user'] = {
      id: backendUser.id,
      email: backendUser.email,
      full_name: backendUser.full_name,
      is_superuser: backendUser.is_superuser,
      is_active: backendUser.is_active,
      created_at: backendUser.created_at,
      updated_at: backendUser.updated_at,
    };

    return {
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      token_type: data.token_type,
      user,
    };
  },

  refresh: async (refreshToken: string): Promise<RefreshTokenResponse> => {
    const { data } = await apiClient.post<RefreshTokenResponse>('/api/auth/refresh', {
      refresh_token: refreshToken,
    });
    return data;
  },

  logout: async (): Promise<void> => {
    // Call logout endpoint if backend has one
    // await apiClient.post('/api/auth/logout');

    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
};
