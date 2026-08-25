/**
 * PP ↔ Token swap API client.
 */
import apiClient from '@/lib/api';

// ── Types ────────────────────────────────────────────────────────────────────

export interface SwapQuote {
  pp_amount: number;
  fee_pp: number;
  fee_percent: number;
  net_pp: number;
  token_amount: number;
  rate: number;
  direction: string;
}

export interface SwapResult {
  swap_id: string;
  pp_amount: number;
  fee_pp: number;
  token_amount: number;
  direction: string;
  rate: number;
  status: string;
  created_at: string | null;
}

export interface SwapHistoryItem {
  id: string;
  amount: number;
  transaction_type: string;
  reason: string;
  created_at: string | null;
}

export interface SwapHistory {
  items: SwapHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ── API calls ────────────────────────────────────────────────────────────────

export const swapAPI = {
  /** Get a preview quote for a swap */
  getQuote: async (ppAmount: number, direction: string = 'pp_to_token'): Promise<SwapQuote> => {
    const { data } = await apiClient.get('/swap/quote', {
      params: { pp_amount: ppAmount, direction },
    });
    return data;
  },

  /** Execute a swap */
  executeSwap: async (
    ppAmount: number,
    direction: string = 'pp_to_token',
    quoteId?: string,
  ): Promise<SwapResult> => {
    const { data } = await apiClient.post('/swap/execute', {
      pp_amount: ppAmount,
      direction,
      quote_id: quoteId,
    });
    return data;
  },

  /** Get swap transaction history */
  getHistory: async (page: number = 1, pageSize: number = 20): Promise<SwapHistory> => {
    const { data } = await apiClient.get('/swap/history', {
      params: { page, page_size: pageSize },
    });
    return data;
  },
};
