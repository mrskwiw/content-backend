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


export interface ValidationBlockedTemplate {
  template_id: string;
  template_name: string;
  error_message: string;
  missing_fields: string[];
}

export interface ValidationWarning {
  template_id: string;
  template_name: string;
  warning_message: string;
  missing_recommended_fields: string[];
  missing_research_tools: string[];
}

export interface TemplateValidationResponse {
  can_generate: boolean;
  blocked_templates: ValidationBlockedTemplate[];
  warnings: ValidationWarning[];
  errors: string[];
}

const TemplateValidationResponseSchema = z.object({
  can_generate: z.boolean(),
  blocked_templates: z.array(z.object({
    template_id: z.string(),
    template_name: z.string(),
    error_message: z.string(),
    missing_fields: z.array(z.string()),
  })),
  warnings: z.array(z.object({
    template_id: z.string(),
    template_name: z.string(),
    warning_message: z.string(),
    missing_recommended_fields: z.array(z.string()),
    missing_research_tools: z.array(z.string()),
  })),
  errors: z.array(z.string()),
});

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
