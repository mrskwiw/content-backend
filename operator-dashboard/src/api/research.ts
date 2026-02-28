import apiClient from './client';

export interface ResearchTool {
  name: string;
  label: string;
  price?: number;
  status?: 'available' | 'coming_soon';
  description?: string;
  category?: string;
}

export interface RunResearchInput {
  projectId: string;
  clientId: string;
  tool: string;
  params?: Record<string, unknown>;
}

export interface ResearchRunResult {
  tool: string;
  outputs: Record<string, string>;
  metadata?: Record<string, unknown>;
}

export interface ResearchResultHistory {
  id: string;
  toolName: string;
  toolLabel?: string;
  createdAt: string;  // ISO 8601
  status: string;
  durationSeconds?: number;
}

export interface ResearchHistoryResponse {
  results: ResearchResultHistory[];
  total: number;
  clientId: string;
}

export const researchApi = {
  async listTools() {
    const { data } = await apiClient.get<ResearchTool[]>('/api/research/tools');
    return data;
  },

  async run(input: RunResearchInput) {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput = {
      project_id: input.projectId,
      client_id: input.clientId,
      tool: input.tool,
      params: input.params,
    };
    const { data } = await apiClient.post<ResearchRunResult>('/api/research/run', backendInput);
    return data;
  },

  async getClientHistory(clientId: string, toolName?: string) {
    const params = toolName ? { tool_name: toolName } : {};
    const { data } = await apiClient.get<ResearchHistoryResponse>(
      `/api/research/results/client/${clientId}`,
      { params }
    );
    return data;
  },
};
