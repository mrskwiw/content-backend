import { apiClient } from './client';

export interface Communication {
  id: number;
  client_id: number;
  user_id: number;
  type: string;  // 'email' | 'call' | 'meeting' | 'note'
  subject: string;
  content: string;
  direction: string;  // 'inbound' | 'outbound'
  duration: string;
  created_at: string;
}

export interface CreateCommunicationInput {
  client_id: number;
  type: string;
  subject: string;
  content?: string;
  direction?: string;
  duration?: string;
}

export const communicationsApi = {
  /**
   * Get all communications for a client
   */
  async listClientCommunications(clientId: string): Promise<Communication[]> {
    const response = await apiClient.get(`/clients/${clientId}/communications`);
    return response.data;
  },

  /**
   * Create a new communication record
   */
  async create(input: CreateCommunicationInput): Promise<Communication> {
    const response = await apiClient.post('/communications', input);
    return response.data;
  },

  /**
   * Delete a communication
   */
  async delete(communicationId: number): Promise<void> {
    await apiClient.delete(`/communications/${communicationId}`);
  },
};
