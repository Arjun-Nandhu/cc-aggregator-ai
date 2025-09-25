const { Configuration, PlaidApi, PlaidEnvironments } = require('plaid');
require('dotenv').config();

// Initialize Plaid client
const configuration = new Configuration({
  basePath: PlaidEnvironments[process.env.PLAID_ENV || 'sandbox'],
  baseOptions: {
    headers: {
      'PLAID-CLIENT-ID': process.env.PLAID_CLIENT_ID,
      'PLAID-SECRET': process.env.PLAID_SECRET,
    },
  },
});

const plaidClient = new PlaidApi(configuration);

class PlaidService {
  // Create a Link token for connecting bank accounts
  async createLinkToken(userId) {
    try {
      const request = {
        user: {
          client_user_id: userId,
        },
        client_name: 'Financial AI App',
        products: ['transactions', 'accounts', 'liabilities'],
        country_codes: ['US'],
        language: 'en',
        webhook: `${process.env.BACKEND_URL || 'http://localhost:5000'}/api/webhooks/plaid`,
      };

      const response = await plaidClient.linkTokenCreate(request);
      return response.data;
    } catch (error) {
      console.error('Error creating link token:', error);
      throw new Error('Failed to create link token');
    }
  }

  // Exchange public token for access token
  async exchangePublicToken(publicToken) {
    try {
      const request = {
        public_token: publicToken,
      };

      const response = await plaidClient.itemPublicTokenExchange(request);
      return response.data;
    } catch (error) {
      console.error('Error exchanging public token:', error);
      throw new Error('Failed to exchange public token');
    }
  }

  // Get accounts for an item
  async getAccounts(accessToken) {
    try {
      const request = {
        access_token: accessToken,
      };

      const response = await plaidClient.accountsGet(request);
      return response.data;
    } catch (error) {
      console.error('Error fetching accounts:', error);
      throw new Error('Failed to fetch accounts');
    }
  }

  // Get transactions for an item
  async getTransactions(accessToken, startDate, endDate, accountIds = null) {
    try {
      const request = {
        access_token: accessToken,
        start_date: startDate,
        end_date: endDate,
        options: {
          include_personal_finance_category: true,
          include_logo_and_counterparty_beta: true,
        },
      };

      if (accountIds) {
        request.account_ids = accountIds;
      }

      const response = await plaidClient.transactionsGet(request);
      return response.data;
    } catch (error) {
      console.error('Error fetching transactions:', error);
      throw new Error('Failed to fetch transactions');
    }
  }

  // Get account balances
  async getBalances(accessToken) {
    try {
      const request = {
        access_token: accessToken,
      };

      const response = await plaidClient.accountsBalanceGet(request);
      return response.data;
    } catch (error) {
      console.error('Error fetching balances:', error);
      throw new Error('Failed to fetch balances');
    }
  }

  // Get item (connection) information
  async getItem(accessToken) {
    try {
      const request = {
        access_token: accessToken,
      };

      const response = await plaidClient.itemGet(request);
      return response.data;
    } catch (error) {
      console.error('Error fetching item info:', error);
      throw new Error('Failed to fetch item information');
    }
  }

  // Update webhook for an item
  async updateWebhook(accessToken, webhookUrl) {
    try {
      const request = {
        access_token: accessToken,
        webhook: webhookUrl,
      };

      const response = await plaidClient.itemWebhookUpdate(request);
      return response.data;
    } catch (error) {
      console.error('Error updating webhook:', error);
      throw new Error('Failed to update webhook');
    }
  }

  // Remove an item (disconnect account)
  async removeItem(accessToken) {
    try {
      const request = {
        access_token: accessToken,
      };

      const response = await plaidClient.itemRemove(request);
      return response.data;
    } catch (error) {
      console.error('Error removing item:', error);
      throw new Error('Failed to remove item');
    }
  }

  // Get institutions by name
  async searchInstitutions(query, products = ['transactions'], countryCodes = ['US']) {
    try {
      const request = {
        query,
        products,
        country_codes: countryCodes,
      };

      const response = await plaidClient.institutionsSearch(request);
      return response.data;
    } catch (error) {
      console.error('Error searching institutions:', error);
      throw new Error('Failed to search institutions');
    }
  }

  // Get institution by ID
  async getInstitution(institutionId) {
    try {
      const request = {
        institution_id: institutionId,
        country_codes: ['US'],
      };

      const response = await plaidClient.institutionsGetById(request);
      return response.data;
    } catch (error) {
      console.error('Error fetching institution:', error);
      throw new Error('Failed to fetch institution');
    }
  }

  // Sync transactions (for periodic updates)
  async syncTransactions(accessToken, cursor = null) {
    try {
      const request = {
        access_token: accessToken,
      };

      if (cursor) {
        request.cursor = cursor;
      } else {
        request.options = {
          include_personal_finance_category: true,
          include_logo_and_counterparty_beta: true,
        };
      }

      const response = await plaidClient.transactionsSync(request);
      return response.data;
    } catch (error) {
      console.error('Error syncing transactions:', error);
      throw new Error('Failed to sync transactions');
    }
  }
}

module.exports = new PlaidService();