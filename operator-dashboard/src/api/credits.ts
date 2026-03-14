import apiClient from './client';

export interface CreditBalance {
  balance: number;
  total_purchased: number;
  total_used: number;
  is_enterprise: boolean;
  custom_credit_rate: number | null;
}

export interface CreditPackage {
  id: string;
  name: string;
  credits: number;
  price_usd: number;
  package_type: 'package' | 'additional';
  is_active: boolean;
  rate_per_credit: number;
  description: string | null;
}

export interface CreditTransaction {
  id: string;
  user_id: string;
  amount: number;
  transaction_type: 'purchase' | 'deduction' | 'refund' | 'admin_adjustment';
  description: string;
  reference_id: string | null;
  reference_type: string | null;
  created_at: string;
}

export const creditsApi = {
  async getBalance() {
    const { data } = await apiClient.get<CreditBalance>('/api/credits/balance');
    return data;
  },

  async getPackages(packageType?: 'package' | 'additional') {
    const params = packageType ? { package_type: packageType } : {};
    const { data } = await apiClient.get<CreditPackage[]>('/api/credits/packages', { params });
    return data;
  },

  async getTransactions(limit = 50, offset = 0, transactionType?: string) {
    const params = { limit, offset, transaction_type: transactionType };
    const { data } = await apiClient.get<CreditTransaction[]>('/api/credits/transactions', {
      params,
    });
    return data;
  },

  async purchaseCredits(packageId: string, paymentReference?: string) {
    const { data } = await apiClient.post('/api/credits/purchase', {
      package_id: packageId,
      payment_reference: paymentReference,
    });
    return data;
  },
};
