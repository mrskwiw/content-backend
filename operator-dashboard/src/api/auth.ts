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
    const user = {

      id: backendUser.id,
      email: backendUser.email,
      fullName: (backendUser as any).fullName || (backendUser as any).full_name,
      isSuperuser: (backendUser as any).isSuperuser || (backendUser as any).is_superuser,
      isActive: (backendUser as any).isActive || (backendUser as any).is_active,
      createdAt: (backendUser as any).createdAt || (backendUser as any).created_at,
      updatedAt: (backendUser as any).updatedAt || (backendUser as any).updated_at,

    } as unknown as LoginResponse['user'];

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
