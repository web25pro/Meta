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

// Products are fetched from the backend via /marketplace/catalog.
// No hardcoded fallback — show empty state when API returns nothing.

export const INPUT_LABEL: Record<RedeemInput, string | null> = {
  phone: 'Phone number',
  meter: 'Meter number',
  smartcard: 'Smartcard / IUC number',
  email: 'Delivery email',
  none: null,
};
