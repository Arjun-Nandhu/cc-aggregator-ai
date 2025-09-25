const express = require('express');
const { body, validationResult } = require('express-validator');
const { authenticateToken, requireOwnership } = require('../middleware/auth');
const { Account } = require('../models');
const plaidService = require('../services/plaidService');

const router = express.Router();

// All routes require authentication
router.use(authenticateToken);

// Get all accounts for the authenticated user
router.get('/', async (req, res) => {
  try {
    const accounts = await Account.findAll({
      where: { userId: req.user.id },
      order: [['institutionName', 'ASC'], ['accountName', 'ASC']]
    });

    res.json({
      accounts: accounts.map(account => ({
        id: account.id,
        plaidAccountId: account.plaidAccountId,
        institutionId: account.institutionId,
        institutionName: account.institutionName,
        accountName: account.accountName,
        accountType: account.accountType,
        accountSubtype: account.accountSubtype,
        accountNumberMasked: account.accountNumberMasked,
        routingNumberMasked: account.routingNumberMasked,
        balanceCurrent: account.balanceCurrent,
        balanceAvailable: account.balanceAvailable,
        balanceLimit: account.balanceLimit,
        currencyCode: account.currencyCode,
        isActive: account.isActive,
        isConnected: account.isConnected,
        lastSyncAt: account.lastSyncAt,
        createdAt: account.createdAt
      }))
    });
  } catch (error) {
    console.error('Get accounts error:', error);
    res.status(500).json({
      error: 'Failed to fetch accounts',
      message: 'Unable to retrieve accounts'
    });
  }
});

// Get account by ID (with ownership check)
router.get('/:accountId', requireOwnership('accountId'), async (req, res) => {
  try {
    const account = await Account.findOne({
      where: {
        id: req.params.accountId,
        userId: req.user.id
      }
    });

    if (!account) {
      return res.status(404).json({
        error: 'Account not found',
        message: 'Account not found'
      });
    }

    res.json({ account });
  } catch (error) {
    console.error('Get account error:', error);
    res.status(500).json({
      error: 'Failed to fetch account',
      message: 'Unable to retrieve account'
    });
  }
});

// Create link token for Plaid Link
router.post('/link-token', async (req, res) => {
  try {
    const linkTokenData = await plaidService.createLinkToken(req.user.id);

    res.json({
      linkToken: linkTokenData.link_token,
      expiration: linkTokenData.expiration
    });
  } catch (error) {
    console.error('Create link token error:', error);
    res.status(500).json({
      error: 'Failed to create link token',
      message: 'Unable to initialize bank connection'
    });
  }
});

// Exchange public token for account access
router.post('/exchange-token', [
  body('publicToken').notEmpty().withMessage('Public token is required')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { publicToken } = req.body;

    // Exchange public token for access token
    const tokenResponse = await plaidService.exchangePublicToken(publicToken);

    // Get accounts from Plaid
    const accountsResponse = await plaidService.getAccounts(tokenResponse.access_token);

    // Get item (institution) information
    const itemResponse = await plaidService.getItem(tokenResponse.access_token);

    // Create account records in database
    const createdAccounts = [];
    for (const plaidAccount of accountsResponse.accounts) {
      const accountData = {
        userId: req.user.id,
        plaidAccountId: plaidAccount.account_id,
        institutionId: itemResponse.item.institution_id,
        institutionName: accountsResponse.item.institution_name,
        accountName: plaidAccount.name,
        accountType: this.mapPlaidAccountType(plaidAccount.type),
        accountSubtype: plaidAccount.subtype,
        accountNumberMasked: plaidAccount.mask,
        currencyCode: plaidAccount.balances.iso_currency_code || 'USD'
      };

      // Check if account already exists
      const existingAccount = await Account.findOne({
        where: {
          userId: req.user.id,
          plaidAccountId: plaidAccount.account_id
        }
      });

      if (existingAccount) {
        // Update existing account
        await existingAccount.update(accountData);
        createdAccounts.push(existingAccount);
      } else {
        // Create new account
        const account = await Account.create(accountData);
        createdAccounts.push(account);
      }
    }

    res.json({
      message: 'Account connected successfully',
      accounts: createdAccounts.map(account => ({
        id: account.id,
        name: account.accountName,
        type: account.accountType,
        institution: account.institutionName
      }))
    });
  } catch (error) {
    console.error('Exchange token error:', error);
    res.status(500).json({
      error: 'Failed to connect account',
      message: 'Unable to connect bank account'
    });
  }
});

// Sync account balances
router.post('/:accountId/sync', requireOwnership('accountId'), async (req, res) => {
  try {
    const account = await Account.findOne({
      where: {
        id: req.params.accountId,
        userId: req.user.id
      }
    });

    if (!account) {
      return res.status(404).json({
        error: 'Account not found',
        message: 'Account not found'
      });
    }

    // Get balances from Plaid
    const balancesResponse = await plaidService.getBalances(account.plaidAccountId);

    // Update account balances
    await account.update({
      balanceCurrent: balancesResponse.accounts[0].balances.current,
      balanceAvailable: balancesResponse.accounts[0].balances.available,
      balanceLimit: balancesResponse.accounts[0].balances.limit,
      lastSyncAt: new Date()
    });

    res.json({
      message: 'Account synced successfully',
      account: {
        id: account.id,
        balanceCurrent: account.balanceCurrent,
        balanceAvailable: account.balanceAvailable,
        balanceLimit: account.balanceLimit,
        lastSyncAt: account.lastSyncAt
      }
    });
  } catch (error) {
    console.error('Sync account error:', error);
    res.status(500).json({
      error: 'Failed to sync account',
      message: 'Unable to sync account data'
    });
  }
});

// Disconnect account
router.delete('/:accountId', requireOwnership('accountId'), async (req, res) => {
  try {
    const account = await Account.findOne({
      where: {
        id: req.params.accountId,
        userId: req.user.id
      }
    });

    if (!account) {
      return res.status(404).json({
        error: 'Account not found',
        message: 'Account not found'
      });
    }

    // Soft delete - mark as inactive
    await account.update({
      isActive: false,
      isConnected: false
    });

    res.json({
      message: 'Account disconnected successfully'
    });
  } catch (error) {
    console.error('Disconnect account error:', error);
    res.status(500).json({
      error: 'Failed to disconnect account',
      message: 'Unable to disconnect account'
    });
  }
});

// Helper function to map Plaid account types to our enum
function mapPlaidAccountType(plaidType) {
  const typeMap = {
    'depository': 'checking',
    'credit': 'credit_card',
    'loan': 'loan',
    'mortgage': 'mortgage',
    'investment': 'investment',
    'brokerage': 'investment'
  };

  return typeMap[plaidType] || 'other';
}

module.exports = router;