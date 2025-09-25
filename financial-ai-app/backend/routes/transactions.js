const express = require('express');
const { body, param, query, validationResult } = require('express-validator');
const { authenticateToken } = require('../middleware/auth');
const { Transaction, Account } = require('../models');
const plaidService = require('../services/plaidService');
const aiAnalysisService = require('../services/aiAnalysisService');

const router = express.Router();

// All routes require authentication
router.use(authenticateToken);

// Get transactions with filtering and pagination
router.get('/', [
  query('startDate').optional().isISO8601().withMessage('Start date must be valid ISO date'),
  query('endDate').optional().isISO8601().withMessage('End date must be valid ISO date'),
  query('accountId').optional().isUUID().withMessage('Account ID must be valid UUID'),
  query('category').optional().isString().withMessage('Category must be string'),
  query('merchant').optional().isString().withMessage('Merchant must be string'),
  query('type').optional().isIn(['debit', 'credit', 'transfer', 'fee', 'interest', 'other']).withMessage('Invalid transaction type'),
  query('limit').optional().isInt({ min: 1, max: 1000 }).withMessage('Limit must be between 1 and 1000'),
  query('offset').optional().isInt({ min: 0 }).withMessage('Offset must be non-negative integer'),
  query('sortBy').optional().isIn(['date', 'amount', 'merchantName']).withMessage('Invalid sort field'),
  query('sortOrder').optional().isIn(['ASC', 'DESC']).withMessage('Sort order must be ASC or DESC')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const {
      startDate,
      endDate,
      accountId,
      category,
      merchant,
      type,
      limit = 50,
      offset = 0,
      sortBy = 'date',
      sortOrder = 'DESC'
    } = req.query;

    // Build where clause
    const whereClause = { userId: req.user.id };

    if (startDate && endDate) {
      whereClause.date = { [require('sequelize').Op.between]: [startDate, endDate] };
    } else if (startDate) {
      whereClause.date = { [require('sequelize').Op.gte]: startDate };
    } else if (endDate) {
      whereClause.date = { [require('sequelize').Op.lte]: endDate };
    }

    if (accountId) whereClause.accountId = accountId;
    if (category) whereClause.category = { [require('sequelize').Op.contains]: [category] };
    if (merchant) whereClause.merchantName = { [require('sequelize').Op.iLike]: `%${merchant}%` };
    if (type) whereClause.transactionType = type;

    // Get transactions
    const transactions = await Transaction.findAndCountAll({
      where: whereClause,
      limit: parseInt(limit),
      offset: parseInt(offset),
      order: [[sortBy, sortOrder]],
      include: [
        {
          model: Account,
          as: 'account',
          attributes: ['accountName', 'institutionName', 'accountType']
        }
      ]
    });

    res.json({
      transactions: transactions.rows,
      pagination: {
        total: transactions.count,
        limit: parseInt(limit),
        offset: parseInt(offset),
        hasMore: offset + limit < transactions.count
      }
    });
  } catch (error) {
    console.error('Get transactions error:', error);
    res.status(500).json({
      error: 'Failed to fetch transactions',
      message: 'Unable to retrieve transactions'
    });
  }
});

// Get transaction by ID
router.get('/:transactionId', [
  param('transactionId').isUUID().withMessage('Transaction ID must be valid UUID')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const transaction = await Transaction.findOne({
      where: {
        id: req.params.transactionId,
        userId: req.user.id
      },
      include: [
        {
          model: Account,
          as: 'account',
          attributes: ['accountName', 'institutionName', 'accountType']
        }
      ]
    });

    if (!transaction) {
      return res.status(404).json({
        error: 'Transaction not found',
        message: 'Transaction not found'
      });
    }

    res.json({ transaction });
  } catch (error) {
    console.error('Get transaction error:', error);
    res.status(500).json({
      error: 'Failed to fetch transaction',
      message: 'Unable to retrieve transaction'
    });
  }
});

// Sync transactions from Plaid
router.post('/sync', [
  body('accountId').optional().isUUID().withMessage('Account ID must be valid UUID'),
  body('startDate').optional().isISO8601().withMessage('Start date must be valid ISO date'),
  body('endDate').optional().isISO8601().withMessage('End date must be valid ISO date')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { accountId, startDate, endDate } = req.body;

    // Get accounts to sync
    let accountsToSync;
    if (accountId) {
      const account = await Account.findOne({
        where: { id: accountId, userId: req.user.id }
      });
      if (!account) {
        return res.status(404).json({
          error: 'Account not found',
          message: 'Account not found'
        });
      }
      accountsToSync = [account];
    } else {
      accountsToSync = await Account.findAll({
        where: { userId: req.user.id, isActive: true }
      });
    }

    const syncResults = [];

    for (const account of accountsToSync) {
      try {
        // Get transactions from Plaid
        const transactionsResponse = await plaidService.getTransactions(
          account.plaidAccountId,
          startDate || '30 days ago',
          endDate || new Date().toISOString().split('T')[0]
        );

        let syncedCount = 0;

        // Process transactions
        for (const plaidTransaction of transactionsResponse.transactions) {
          const transactionData = {
            userId: req.user.id,
            accountId: account.id,
            plaidTransactionId: plaidTransaction.transaction_id,
            amount: plaidTransaction.amount,
            currencyCode: plaidTransaction.iso_currency_code || 'USD',
            date: plaidTransaction.date,
            datetime: plaidTransaction.datetime,
            merchantName: plaidTransaction.merchant_name,
            merchantCategory: plaidTransaction.merchant_category,
            category: plaidTransaction.category,
            subcategory: plaidTransaction.subcategory,
            description: plaidTransaction.name,
            location: plaidTransaction.location,
            paymentMethod: plaidTransaction.payment_method,
            paymentChannel: plaidTransaction.payment_channel,
            transactionType: this.mapPlaidTransactionType(plaidTransaction.amount),
            pending: plaidTransaction.pending
          };

          // Check if transaction already exists
          const existingTransaction = await Transaction.findOne({
            where: {
              userId: req.user.id,
              plaidTransactionId: plaidTransaction.transaction_id
            }
          });

          if (existingTransaction) {
            // Update existing transaction
            await existingTransaction.update(transactionData);
          } else {
            // Create new transaction
            await Transaction.create(transactionData);
            syncedCount++;
          }
        }

        syncResults.push({
          accountId: account.id,
          accountName: account.accountName,
          syncedTransactions: syncedCount,
          totalTransactions: transactionsResponse.transactions.length
        });

        // Update account last sync time
        await account.update({ lastSyncAt: new Date() });

      } catch (error) {
        console.error(`Error syncing account ${account.id}:`, error);
        syncResults.push({
          accountId: account.id,
          accountName: account.accountName,
          error: error.message
        });
      }
    }

    res.json({
      message: 'Transaction sync completed',
      results: syncResults
    });
  } catch (error) {
    console.error('Sync transactions error:', error);
    res.status(500).json({
      error: 'Failed to sync transactions',
      message: 'Unable to sync transaction data'
    });
  }
});

// Analyze transaction with AI
router.post('/:transactionId/analyze', [
  param('transactionId').isUUID().withMessage('Transaction ID must be valid UUID')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const transaction = await Transaction.findOne({
      where: {
        id: req.params.transactionId,
        userId: req.user.id
      }
    });

    if (!transaction) {
      return res.status(404).json({
        error: 'Transaction not found',
        message: 'Transaction not found'
      });
    }

    // Analyze transaction with AI
    const analysis = await aiAnalysisService.analyzeTransaction(transaction);

    // Update transaction with analysis
    await transaction.update({
      aiAnalysis: analysis,
      confidence: analysis.confidence
    });

    res.json({
      message: 'Transaction analyzed successfully',
      analysis: analysis
    });
  } catch (error) {
    console.error('Analyze transaction error:', error);
    res.status(500).json({
      error: 'Failed to analyze transaction',
      message: 'Unable to analyze transaction'
    });
  }
});

// Update transaction
router.put('/:transactionId', [
  param('transactionId').isUUID().withMessage('Transaction ID must be valid UUID'),
  body('notes').optional().isString().withMessage('Notes must be string'),
  body('tags').optional().isArray().withMessage('Tags must be array'),
  body('category').optional().isArray().withMessage('Category must be array')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const transaction = await Transaction.findOne({
      where: {
        id: req.params.transactionId,
        userId: req.user.id
      }
    });

    if (!transaction) {
      return res.status(404).json({
        error: 'Transaction not found',
        message: 'Transaction not found'
      });
    }

    const { notes, tags, category } = req.body;

    // Update transaction
    await transaction.update({
      notes,
      tags,
      category
    });

    res.json({
      message: 'Transaction updated successfully',
      transaction
    });
  } catch (error) {
    console.error('Update transaction error:', error);
    res.status(500).json({
      error: 'Failed to update transaction',
      message: 'Unable to update transaction'
    });
  }
});

// Delete transaction (soft delete)
router.delete('/:transactionId', [
  param('transactionId').isUUID().withMessage('Transaction ID must be valid UUID')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const transaction = await Transaction.findOne({
      where: {
        id: req.params.transactionId,
        userId: req.user.id
      }
    });

    if (!transaction) {
      return res.status(404).json({
        error: 'Transaction not found',
        message: 'Transaction not found'
      });
    }

    // Soft delete by setting deletedAt
    await transaction.destroy();

    res.json({
      message: 'Transaction deleted successfully'
    });
  } catch (error) {
    console.error('Delete transaction error:', error);
    res.status(500).json({
      error: 'Failed to delete transaction',
      message: 'Unable to delete transaction'
    });
  }
});

// Helper function to map Plaid transaction amounts to types
function mapPlaidTransactionType(amount) {
  if (amount < 0) return 'debit';
  if (amount > 0) return 'credit';
  return 'other';
}

module.exports = router;