/**
 * Cost API Client
 *
 * Provides access to token usage and cost reporting endpoints.
 */
import apiClient from './client';

export interface ProjectCostSummary {
  projectId: string;
  projectName: string;
  totalRuns: number;
  totalPosts: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCacheCreationTokens: number;
  totalCacheReadTokens: number;
  totalGenerationCostUsd: number;
  totalResearchTools: number;
  totalResearchCostUsd: number;
  totalCostUsd: number;
  costPerPost: number | null;
}

export interface RunCostBreakdown {
  runId: string;
  projectId: string;
  status: string;
  startedAt: string;
  completedAt: string | null;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCacheCreationTokens: number;
  totalCacheReadTokens: number;
  totalCostUsd: number;
  estimatedCostUsd: number | null;
  totalPosts: number;
  postsWithTokenData: number;
  avgCostPerPost: number | null;
  cacheSavingsUsd: number | null;
}

export interface CostTrend {
  date: string;
  costUsd: number;
}

export interface UserCostSummary {
  userId: string;
  periodDays: number;
  totalProjects: number;
  totalRuns: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalGenerationCostUsd: number;
  totalResearchTools: number;
  totalResearchCostUsd: number;
  totalCostUsd: number;
  topProjects: Array<{
    projectId: string;
    projectName: string;
    costUsd: number;
  }>;
  costTrend: CostTrend[];
}

export interface ResearchCostSummary {
  clientId: string;
  clientName: string;
  totalResearchTools: number;
  totalBusinessPriceUsd: number;
  totalActualCostUsd: number;
  priceDifferenceUsd: number;
  toolsBreakdown: Array<{
    toolName: string;
    toolLabel: string;
    executionCount: number;
    totalBusinessPrice: number;
    totalActualCost: number;
    totalTokens: number;
  }>;
}

export const costsApi = {
  /**
   * Get cost summary for a project
   */
  async getProjectCosts(projectId: string): Promise<ProjectCostSummary> {
    const response = await apiClient.get(`/api/costs/project/${projectId}`);
    return response.data;
  },

  /**
   * Get detailed cost breakdown for a run
   */
  async getRunCosts(runId: string): Promise<RunCostBreakdown> {
    const response = await apiClient.get(`/api/costs/run/${runId}`);
    return response.data;
  },

  /**
   * Get user-wide cost summary with trends
   */
  async getUserCostSummary(days: number = 30): Promise<UserCostSummary> {
    const response = await apiClient.get('/api/costs/summary', {
      params: { days },
    });
    return response.data;
  },

  /**
   * Get research cost summary for a client
   */
  async getResearchCosts(clientId: string): Promise<ResearchCostSummary> {
    const response = await apiClient.get(`/api/costs/research/${clientId}`);
    return response.data;
  },

  /**
   * Format token count with commas
   */
  formatTokens(tokens: number): string {
    return tokens.toLocaleString();
  },

  /**
   * Format USD cost with $ and 4 decimal places
   */
  formatCost(costUsd: number): string {
    return `$${costUsd.toFixed(4)}`;
  },

  /**
   * Format USD cost for display (2 decimals for larger amounts)
   */
  formatCostDisplay(costUsd: number): string {
    if (costUsd >= 1) {
      return `$${costUsd.toFixed(2)}`;
    }
    return `$${costUsd.toFixed(4)}`;
  },

  /**
   * Calculate cache savings percentage
   */
  calculateCacheSavingsPercent(
    cacheReadTokens: number,
    totalInputTokens: number
  ): number {
    if (totalInputTokens === 0) return 0;
    return (cacheReadTokens / totalInputTokens) * 100;
  },
};
