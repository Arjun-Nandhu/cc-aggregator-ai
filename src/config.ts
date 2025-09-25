import 'dotenv/config';

export type AppConfig = {
  port: number;
  plaidEnv: 'sandbox' | 'development' | 'production';
  plaidClientId: string;
  plaidSecret: string;
  plaidProducts: string[];
  plaidCountryCodes: string[];
  plaidRedirectUri?: string;
};

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value || value.trim() === '') {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const config: AppConfig = {
  port: Number(process.env.PORT ?? 3000),
  plaidEnv: (process.env.PLAID_ENV ?? 'sandbox') as AppConfig['plaidEnv'],
  plaidClientId: requireEnv('PLAID_CLIENT_ID'),
  plaidSecret: requireEnv('PLAID_SECRET'),
  plaidProducts: (process.env.PLAID_PRODUCTS ?? 'transactions').split(',').map(s => s.trim()).filter(Boolean),
  plaidCountryCodes: (process.env.PLAID_COUNTRY_CODES ?? 'US').split(',').map(s => s.trim()).filter(Boolean),
  ...(process.env.PLAID_REDIRECT_URI ? { plaidRedirectUri: process.env.PLAID_REDIRECT_URI } : {}),
};

