import apiClient from './client';
import { ResearchResult } from '../types/domain';

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

export interface ResearchResultListResponse {
  results: ResearchResult[];
  total: number;
  clientId?: string;
  projectId?: string;
}

export interface NextBundleSuggestion {
  bundle: string;
  bundleName: string;
  missingTools: string[];
  missingToolNames: string[];
  additionalCost: number;
  potentialSavings: number;
}

export interface PricingPreview {
  baseCost: number;
  discount: number;
  finalCost: number;
  bundleApplied: string | null;
  bundleName: string | null;
  savingsPercent: number;
  nextBundleSuggestion?: NextBundleSuggestion;
}

export interface ToolStats {
  toolName: string;
  toolLabel: string;
  executionCount: number;
  totalRevenue: number;
  totalApiCost: number;
}

export interface ResearchAnalytics {
  totalRevenue: number;
  totalApiCost: number;
  profitMargin: number;
  totalExecutions: number;
  cacheHitRate: number;
  cacheSavings: number;
  avgCostPerTool: number;
  topTools: ToolStats[];
  dateRange: number;
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
    const { data} = await apiClient.post<ResearchRunResult>('/api/research/run', backendInput);
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

  /**
   * Fetch full research results for a client (includes outputs, data, etc.)
   * Returns full response with results array, total count, and IDs
   */
  async getClientResearchResults(clientId: string, toolName?: string): Promise<ResearchResultListResponse> {
    const params = toolName ? { tool_name: toolName } : {};
    const { data } = await apiClient.get<ResearchResultListResponse>(
      `/api/research/results/client/${clientId}`,
      { params }
    );
    return data;
  },

  /**
   * Fetch full research results for a project (includes outputs, data, etc.)
   * Returns full response with results array, total count, and IDs
   */
  async getProjectResearchResults(projectId: string, toolName?: string): Promise<ResearchResultListResponse> {
    const params = toolName ? { tool_name: toolName } : {};
    const { data } = await apiClient.get<ResearchResultListResponse>(
      `/api/research/results/project/${projectId}`,
      { params }
    );
    return data;
  },

  /**
   * Fetch the content of a research result output file
   */
  async getResearchOutputContent(
    resultId: string,
    outputFormat: string
  ): Promise<{ content: string; format: string }> {
    const { data } = await apiClient.get<{ content: string; format: string }>(
      `/api/research/results/${resultId}/output/${outputFormat}`
    );
    return data;
  },

  /**
   * Delete a research result
   */
  async deleteResult(resultId: string): Promise<void> {
    await apiClient.delete(`/api/research/results/${resultId}`);
  },

  /**
   * Get pricing preview with bundle detection
   */
  async getPricingPreview(toolIds: string[]): Promise<PricingPreview> {
    const { data } = await apiClient.get<PricingPreview>('/api/research/pricing-preview', {
      params: { tool_ids: toolIds.join(',') }
    });
    return data;
  },

  /**
   * Get research analytics
   */
  async getAnalytics(days: number = 90): Promise<ResearchAnalytics> {
    const { data } = await apiClient.get<ResearchAnalytics>('/api/research/analytics', {
      params: { days }
    });
    return data;
  },

  /**
   * Get optimal execution order for research tools based on dependencies
   */
  async getExecutionOrder(toolNames: string[]): Promise<{ executionOrder: string[]; toolCount: number }> {
    const { data } = await apiClient.post<{ executionOrder: string[]; toolCount: number }>(
      '/api/research/execution-order',
      { tool_names: toolNames }
    );
    return data;
  },
};
