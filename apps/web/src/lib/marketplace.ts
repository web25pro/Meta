/**
 * Utility Marketplace catalog — VTU + gift cards.
 * Master Prompt v3.0, Chapter 12 (Global Utility Marketplace Directory).
 * 1,000 PP = $10 USD (Chapter 5.1).
 */

export type MarketCategory =
  | 'airtime'
  | 'data'
  | 'electricity'
  | 'cable'
  | 'giftcards';

export type RedeemInput = 'phone' | 'meter' | 'smartcard' | 'email' | 'none';

export interface Product {
  id: string;
  category: MarketCategory;
  name: string;
  /** PP cost. */
  pp: number;
  /** Fiat equivalent label. */
  fiat: string;
  provider: string;
  regions: string[];
  input: RedeemInput;
}

export const CATEGORIES: { key: MarketCategory; label: string; blurb: string }[] = [
  { key: 'airtime', label: 'Airtime', blurb: 'Top up any mobile number instantly' },
  { key: 'data', label: 'Data', blurb: 'Mobile data bundles across regions' },
  { key: 'electricity', label: 'Electricity', blurb: 'Prepaid meter tokens' },
  { key: 'cable', label: 'Cable & WiFi', blurb: 'TV subscriptions and WiFi vouchers' },
  { key: 'giftcards', label: 'Gift Cards', blurb: 'Shop anywhere with digital cards' },
];

/** Emoji flag per region code. */
export const FLAG: Record<string, string> = {
  NG: '🇳🇬', GH: '🇬🇭', KE: '🇰🇪', ZA: '🇿🇦', ID: '🇮🇩', PH: '🇵🇭',
  SG: '🇸🇬', AE: '🇦🇪', GB: '🇬🇧', US: '🇺🇸', DE: '🇩🇪', FR: '🇫🇷', TH: '🇹🇭',
};

export const PRODUCTS: Product[] = [
  // ── Airtime (VTU) ──
  { id: 'air-100', category: 'airtime', name: 'Airtime ₦100', pp: 200, fiat: '≈ ₦100', provider: "Africa's Talking", regions: ['NG', 'GH', 'KE', 'ZA'], input: 'phone' },
  { id: 'air-500', category: 'airtime', name: 'Airtime ₦500', pp: 950, fiat: '≈ ₦500', provider: 'Reloadly', regions: ['NG', 'GH', 'KE', 'ZA'], input: 'phone' },
  { id: 'air-1000', category: 'airtime', name: 'Airtime ₦1,000', pp: 1850, fiat: '≈ ₦1,000', provider: 'Reloadly', regions: ['NG', 'GH', 'KE', 'ZA'], input: 'phone' },

  // ── Data (VTU) ──
  { id: 'data-1', category: 'data', name: 'Data Bundle 1GB', pp: 500, fiat: '≈ ₦350', provider: 'Reloadly', regions: ['NG', 'GH', 'ZA', 'ID', 'PH'], input: 'phone' },
  { id: 'data-3', category: 'data', name: 'Data Bundle 3GB', pp: 1300, fiat: '≈ ₦900', provider: 'Reloadly', regions: ['NG', 'GH', 'ZA', 'ID', 'PH'], input: 'phone' },
  { id: 'data-10', category: 'data', name: 'Data Bundle 10GB', pp: 3800, fiat: '≈ ₦3,000', provider: 'Reloadly', regions: ['NG', 'GH', 'ZA', 'ID', 'PH'], input: 'phone' },

  // ── Electricity (VTU) ──
  { id: 'elec-token', category: 'electricity', name: 'Electricity token ₦1,000', pp: 1000, fiat: '≈ ₦1,000', provider: 'Reloadly Utilities', regions: ['NG', 'GH', 'KE'], input: 'meter' },
  { id: 'elec-5k', category: 'electricity', name: 'Electricity token ₦5,000', pp: 4900, fiat: '≈ ₦5,000', provider: 'Reloadly Utilities', regions: ['NG', 'GH', 'KE'], input: 'meter' },

  // ── Cable & WiFi ──
  { id: 'wifi', category: 'cable', name: 'WiFi voucher', pp: 300, fiat: '≈ $3', provider: 'Partner API', regions: ['SG', 'AE', 'GB'], input: 'none' },
  { id: 'dstv', category: 'cable', name: 'Cable TV — Compact', pp: 2400, fiat: '≈ ₦1,900', provider: 'Reloadly', regions: ['NG', 'GH', 'KE', 'ZA'], input: 'smartcard' },

  // ── Gift Cards ──
  { id: 'gc-amazon-10', category: 'giftcards', name: 'Amazon Gift Card $10', pp: 1100, fiat: '$10', provider: 'Reloadly GiftCards', regions: ['US', 'GB', 'DE', 'FR'], input: 'email' },
  { id: 'gc-amazon-25', category: 'giftcards', name: 'Amazon Gift Card $25', pp: 2700, fiat: '$25', provider: 'Reloadly GiftCards', regions: ['US', 'GB', 'DE', 'FR'], input: 'email' },
  { id: 'gc-jumia', category: 'giftcards', name: 'Jumia voucher', pp: 500, fiat: '≈ ₦5,000', provider: 'Jumia API', regions: ['NG', 'GH', 'KE'], input: 'email' },
  { id: 'gc-shopee', category: 'giftcards', name: 'Shopee credits', pp: 500, fiat: '≈ $5', provider: 'Shopee API', regions: ['PH', 'ID', 'SG', 'TH'], input: 'email' },
  { id: 'gc-google', category: 'giftcards', name: 'Google Play $10', pp: 1150, fiat: '$10', provider: 'Reloadly GiftCards', regions: ['US', 'GB', 'NG', 'PH'], input: 'email' },
  { id: 'gc-steam', category: 'giftcards', name: 'Steam Wallet $20', pp: 2200, fiat: '$20', provider: 'Reloadly GiftCards', regions: ['US', 'GB', 'DE', 'TH'], input: 'email' },
];

export const INPUT_LABEL: Record<RedeemInput, string | null> = {
  phone: 'Phone number',
  meter: 'Meter number',
  smartcard: 'Smartcard / IUC number',
  email: 'Delivery email',
  none: null,
};
