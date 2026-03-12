import apiClient from './client';
import type { ExportInput, GenerateAllInput, RegenerateInput, Run } from '@/types/domain';
import type { Deliverable } from '@/types/domain';

export interface TemplateDependencies {
  required: string[];
  recommended: string[];
}

export interface TemplateDependenciesResponse {
  template_number: number;
  template_title: string;
  research_dependencies: TemplateDependencies;
}

export const generatorApi = {
  async generateAll(input: GenerateAllInput) {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput = {
      project_id: input.projectId,
      client_id: input.clientId,
      is_batch: input.isBatch ?? true,
      template_quantities: input.templateQuantities,  // FIX: was missing, causing template distribution to be ignored
      custom_topics: input.customTopics,  // NEW: topic override for content generation
      target_platform: input.targetPlatform,  // NEW: target platform for platform-specific generation
    };
    const { data } = await apiClient.post<Run>('/api/generator/generate-all', backendInput);
    return data;
  },

  async regenerate(input: RegenerateInput) {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput = {
      project_id: input.projectId,
      post_ids: input.postIds,
      reason: input.reason,
    };
    const { data } = await apiClient.post<Run>('/api/generator/regenerate', backendInput);
    return data;
  },

  async exportPackage(input: ExportInput) {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput = {
      project_id: input.projectId,
      client_id: input.clientId,
      format: input.format,
      include_audit_log: input.includeAuditLog,
      include_research: input.includeResearch,
    };
    const { data } = await apiClient.post<Deliverable>('/api/generator/export', backendInput);
    return data;
  },

  async getTemplateDependencies(templateNumber: number) {
    const { data } = await apiClient.get<TemplateDependenciesResponse>(
      `/api/generator/template-dependencies/${templateNumber}`
    );
    return data;
  },
};
