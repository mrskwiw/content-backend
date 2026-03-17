import apiClient from './client';
import { RunSchema, DeliverableSchema, type ExportInput, type GenerateAllInput, type RegenerateInput, type Run, type Deliverable } from '@/types/domain';
import { z } from 'zod';

const TemplateDependenciesSchema = z.object({
  required: z.array(z.string()),
  recommended: z.array(z.string()),
});

const TemplateDependenciesResponseSchema = z.object({
  template_number: z.number(),
  template_title: z.string(),
  research_dependencies: TemplateDependenciesSchema,
});

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
  async generateAll(input: GenerateAllInput): Promise<Run> {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput = {
      project_id: input.projectId,
      client_id: input.clientId,
      is_batch: input.isBatch ?? true,
      template_quantities: input.templateQuantities,  // FIX: was missing, causing template distribution to be ignored
      custom_topics: input.customTopics,  // NEW: topic override for content generation
      target_platform: input.targetPlatform,  // NEW: target platform for platform-specific generation
    };
    const { data } = await apiClient.post('/api/generator/generate-all', backendInput);
    return RunSchema.parse(data);
  },

  async regenerate(input: RegenerateInput): Promise<Run> {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput = {
      project_id: input.projectId,
      post_ids: input.postIds,
      reason: input.reason,
    };
    const { data } = await apiClient.post('/api/generator/regenerate', backendInput);
    return RunSchema.parse(data);
  },

  async exportPackage(input: ExportInput): Promise<Deliverable> {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput = {
      project_id: input.projectId,
      client_id: input.clientId,
      format: input.format,
      include_audit_log: input.includeAuditLog,
      include_research: input.includeResearch,
    };
    const { data } = await apiClient.post('/api/generator/export', backendInput);
    return DeliverableSchema.parse(data);
  },

  async getTemplateDependencies(templateNumber: number): Promise<TemplateDependenciesResponse> {
    const { data } = await apiClient.get(
      `/api/generator/template-dependencies/${templateNumber}`
    );
    return TemplateDependenciesResponseSchema.parse(data);
  },
};
