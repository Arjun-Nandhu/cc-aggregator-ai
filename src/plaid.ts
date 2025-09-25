import { Configuration, PlaidApi, PlaidEnvironments } from 'plaid';
import { config } from './config.js';

function getPlaidBasePath(): string {
  const env = config.plaidEnv;
  const mapping = PlaidEnvironments as unknown as Record<string, string>;
  return (mapping[env] ?? mapping['sandbox']) as string;
}

const plaidConfig = new Configuration({
  basePath: getPlaidBasePath(),
  baseOptions: {
    headers: {
      'PLAID-CLIENT-ID': config.plaidClientId,
      'PLAID-SECRET': config.plaidSecret,
    },
  },
});

export const plaid = new PlaidApi(plaidConfig);

