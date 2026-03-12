/**
 * Settings API - User preferences and integrations
 */

import { apiClient } from './client';

export interface WebSearchConfig {
  provider: 'brave' | 'tavily' | 'stub';
  brave_api_key_configured: boolean;
  tavily_api_key_configured: boolean;
}

export interface WebSearchConfigUpdate {
  provider: 'brave' | 'tavily' | 'stub';
  brave_api_key?: string | null;
  tavily_api_key?: string | null;
}

export interface TestConnectionRequest {
  provider: 'brave' | 'tavily';
  api_key: string;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  provider: string;
  results_count?: number;
}

export const settingsApi = {
  /**
   * Get current web search configuration
   */
  getWebSearchConfig: async (): Promise<WebSearchConfig> => {
    const response = await apiClient.get<WebSearchConfig>('/api/settings/web-search');
    return response.data;
  },

  /**
   * Update web search configuration
   */
  updateWebSearchConfig: async (update: WebSearchConfigUpdate): Promise<WebSearchConfig> => {
    const response = await apiClient.post<WebSearchConfig>('/api/settings/web-search', update);
    return response.data;
  },

  /**
   * Test web search API connection
   */
  testConnection: async (request: TestConnectionRequest): Promise<TestConnectionResponse> => {
    const response = await apiClient.post<TestConnectionResponse>(
      '/api/settings/web-search/test',
      request
    );
    return response.data;
  },

  /**
   * Delete API key for a provider
   */
  deleteApiKey: async (provider: 'brave' | 'tavily'): Promise<void> => {
    await apiClient.delete(`/api/settings/web-search/keys/${provider}`);
  },
};
