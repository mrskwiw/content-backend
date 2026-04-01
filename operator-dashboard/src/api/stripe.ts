import apiClient from './client';

export interface CheckoutSessionRequest {
  package_id: string;
  success_url: string;
  cancel_url: string;
  project_id?: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
}

export interface PaymentStatus {
  session_id: string;
  status: 'pending' | 'completed' | 'failed' | 'expired';
  credits: number | null;
  project_id: string | null;
}

export const stripeApi = {
  async createCheckoutSession(req: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
    const { data } = await apiClient.post('/api/stripe/checkout', req);
    return data;
  },

  async getPaymentStatus(sessionId: string): Promise<PaymentStatus> {
    const { data } = await apiClient.get(`/api/stripe/payment-status/${sessionId}`);
    return data;
  },
};
