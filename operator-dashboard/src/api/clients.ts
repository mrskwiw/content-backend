import apiClient from './client';
import { ClientSchema, type Client, type Platform } from '@/types/domain';
import { z } from 'zod';

export interface CreateClientInput {
  name: string;
  email?: string;
  industry?: string;
  businessDescription?: string;
  idealCustomer?: string;
  mainProblemSolved?: string;
  tonePreference?: string;
  platforms?: Platform[];
  customerPainPoints?: string[];
  customerQuestions?: string[];
  keywords?: string[];
  competitors?: string[];
  location?: string;
}

export interface UpdateClientInput {
  name?: string;
  email?: string;
  industry?: string;
  businessDescription?: string;
  idealCustomer?: string;
  mainProblemSolved?: string;
  tonePreference?: string;
  platforms?: Platform[];
  customerPainPoints?: string[];
  customerQuestions?: string[];
  keywords?: string[];
  competitors?: string[];
  location?: string;
}

export const clientsApi = {
  async list(): Promise<Client[]> {
    const { data } = await apiClient.get('/api/clients/');
    return z.array(ClientSchema).parse(data);
  },

  async get(clientId: string): Promise<Client> {
    const { data } = await apiClient.get(`/api/clients/${clientId}`);
    return ClientSchema.parse(data);
  },

  async create(input: CreateClientInput): Promise<Client> {
    // Convert camelCase to snake_case for backend compatibility
    // Exclude undefined values to prevent validation errors
    const backendInput: Record<string, string | string[] | Platform[] | undefined> = {
      name: input.name,
    };

    if (input.email !== undefined) backendInput.email = input.email;
    if (input.industry !== undefined) backendInput.industry = input.industry;
    if (input.businessDescription !== undefined) backendInput.business_description = input.businessDescription;
    if (input.idealCustomer !== undefined) backendInput.ideal_customer = input.idealCustomer;
    if (input.mainProblemSolved !== undefined) backendInput.main_problem_solved = input.mainProblemSolved;
    if (input.tonePreference !== undefined) backendInput.tone_preference = input.tonePreference;
    if (input.platforms !== undefined) backendInput.platforms = input.platforms;
    if (input.customerPainPoints !== undefined) backendInput.customer_pain_points = input.customerPainPoints;
    if (input.customerQuestions !== undefined) backendInput.customer_questions = input.customerQuestions;

    const { data } = await apiClient.post('/api/clients/', backendInput);
    return ClientSchema.parse(data);
  },

  async update(clientId: string, input: UpdateClientInput): Promise<Client> {
    // Convert camelCase to snake_case for backend compatibility
    const backendInput: Record<string, string | number | string[] | Platform[] | undefined> = {};
    if (input.name !== undefined) backendInput.name = input.name;
    if (input.email !== undefined) backendInput.email = input.email;
    if (input.industry !== undefined) backendInput.industry = input.industry;
    if (input.businessDescription !== undefined) backendInput.business_description = input.businessDescription;
    if (input.idealCustomer !== undefined) backendInput.ideal_customer = input.idealCustomer;
    if (input.mainProblemSolved !== undefined) backendInput.main_problem_solved = input.mainProblemSolved;
    if (input.tonePreference !== undefined) backendInput.tone_preference = input.tonePreference;
    if (input.platforms !== undefined) backendInput.platforms = input.platforms;
    if (input.customerPainPoints !== undefined) backendInput.customer_pain_points = input.customerPainPoints;
    if (input.customerQuestions !== undefined) backendInput.customer_questions = input.customerQuestions;

    const { data } = await apiClient.patch(`/api/clients/${clientId}`, backendInput);
    return ClientSchema.parse(data);
  },

  async exportProfile(clientId: string): Promise<{ blob: Blob; filename: string }> {
    const response = await apiClient.get(`/api/clients/${clientId}/export-profile`, {
      responseType: 'blob',
    });

    // Extract filename from Content-Disposition header if available
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'client_profile.md';

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/"/g, '');
      }
    }

    return {
      blob: response.data,
      filename,
    };
  },
};
