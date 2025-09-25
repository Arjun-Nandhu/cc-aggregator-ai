const OpenAI = require('openai');
require('dotenv').config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

class AIAnalysisService {
  // Analyze a single transaction
  async analyzeTransaction(transaction) {
    try {
      const prompt = `
        Analyze this financial transaction and provide insights:

        Transaction Details:
        - Amount: $${transaction.amount}
        - Merchant: ${transaction.merchantName || 'Unknown'}
        - Description: ${transaction.description || 'No description'}
        - Category: ${transaction.category ? transaction.category.join(' > ') : 'Uncategorized'}
        - Date: ${transaction.date}
        - Type: ${transaction.transactionType}

        Please provide a JSON response with the following structure:
        {
          "category_suggestion": "string - suggested category if different from current",
          "subcategory_suggestion": "string - suggested subcategory",
          "is_recurring": boolean,
          "recurrence_pattern": "object - if recurring, describe the pattern",
          "spending_behavior": "string - analysis of spending behavior",
          "budget_impact": "string - how this affects budget",
          "risk_assessment": "string - any financial risks or concerns",
          "recommendations": "array - list of financial recommendations",
          "confidence": "number between 0 and 1"
        }
      `;

      const completion = await openai.chat.completions.create({
        model: 'gpt-4',
        messages: [
          {
            role: 'system',
            content: 'You are a financial advisor AI. Analyze transactions and provide helpful financial insights in JSON format.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 1000
      });

      const analysis = JSON.parse(completion.choices[0].message.content);
      return analysis;
    } catch (error) {
      console.error('Error analyzing transaction:', error);
      return {
        category_suggestion: null,
        subcategory_suggestion: null,
        is_recurring: false,
        recurrence_pattern: {},
        spending_behavior: 'Unable to analyze transaction',
        budget_impact: 'No impact analysis available',
        risk_assessment: 'No risk assessment available',
        recommendations: [],
        confidence: 0
      };
    }
  }

  // Analyze spending patterns for a user
  async analyzeSpendingPatterns(transactions, timeRange = '30d') {
    try {
      const transactionSummary = this.summarizeTransactions(transactions);

      const prompt = `
        Analyze these spending patterns and provide insights:

        Time Range: ${timeRange}
        Total Transactions: ${transactions.length}
        Total Spending: $${transactionSummary.totalSpending.toFixed(2)}
        Total Income: $${transactionSummary.totalIncome.toFixed(2)}

        Category Breakdown:
        ${Object.entries(transactionSummary.categoryBreakdown)
          .map(([category, data]) => `- ${category}: $${data.total.toFixed(2)} (${data.count} transactions)`)
          .join('\n')}

        Top Merchants:
        ${transactionSummary.topMerchants.slice(0, 10)
          .map(merchant => `- ${merchant.name}: $${merchant.total.toFixed(2)} (${merchant.count} transactions)`)
          .join('\n')}

        Please provide a JSON response with:
        {
          "overall_health": "string - overall financial health assessment",
          "spending_trends": "array - key spending trends identified",
          "budget_analysis": "object - analysis of spending vs recommended budgets",
          "saving_opportunities": "array - opportunities to save money",
          "risk_factors": "array - potential financial risks",
          "recommendations": "array - specific actionable recommendations",
          "score": "number between 0 and 100 - financial health score"
        }
      `;

      const completion = await openai.chat.completions.create({
        model: 'gpt-4',
        messages: [
          {
            role: 'system',
            content: 'You are a financial advisor AI. Provide comprehensive financial analysis and actionable advice.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 1500
      });

      const analysis = JSON.parse(completion.choices[0].message.content);
      return analysis;
    } catch (error) {
      console.error('Error analyzing spending patterns:', error);
      return {
        overall_health: 'Unable to analyze',
        spending_trends: [],
        budget_analysis: {},
        saving_opportunities: [],
        risk_factors: [],
        recommendations: ['Consider consulting with a financial advisor'],
        score: 0
      };
    }
  }

  // Generate financial insights and predictions
  async generateInsights(transactions, userProfile = {}) {
    try {
      const prompt = `
        Based on the transaction data, generate personalized financial insights:

        User Profile:
        - Age: ${userProfile.age || 'Unknown'}
        - Income: ${userProfile.monthlyIncome || 'Unknown'}
        - Financial Goals: ${userProfile.goals ? userProfile.goals.join(', ') : 'Not specified'}

        Recent Transaction Summary:
        - Last 30 days spending: $${this.calculateTotalSpending(transactions, 30).toFixed(2)}
        - Last 30 days income: $${this.calculateTotalIncome(transactions, 30).toFixed(2)}

        Provide insights in JSON format:
        {
          "short_term_insights": "array - insights for the next 1-3 months",
          "long_term_insights": "array - insights for 6-12 months",
          "investment_suggestions": "array - investment recommendations",
          "debt_management": "array - debt reduction strategies",
          "emergency_fund_status": "string - assessment of emergency fund",
          "retirement_planning": "array - retirement planning advice",
          "tax_optimization": "array - tax saving opportunities"
        }
      `;

      const completion = await openai.chat.completions.create({
        model: 'gpt-4',
        messages: [
          {
            role: 'system',
            content: 'You are a comprehensive financial planning AI. Provide detailed, actionable financial insights.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.4,
        max_tokens: 2000
      });

      const insights = JSON.parse(completion.choices[0].message.content);
      return insights;
    } catch (error) {
      console.error('Error generating insights:', error);
      return {
        short_term_insights: ['Track your spending more closely'],
        long_term_insights: ['Build an emergency fund'],
        investment_suggestions: ['Consider low-risk investments'],
        debt_management: ['Pay down high-interest debt first'],
        emergency_fund_status: 'Insufficient data',
        retirement_planning: ['Start saving for retirement'],
        tax_optimization: ['Consult a tax professional']
      };
    }
  }

  // Helper methods
  summarizeTransactions(transactions) {
    const summary = {
      totalSpending: 0,
      totalIncome: 0,
      categoryBreakdown: {},
      topMerchants: []
    };

    const merchantTotals = {};

    transactions.forEach(transaction => {
      const amount = Math.abs(transaction.amount);

      if (transaction.amount < 0) {
        summary.totalSpending += amount;
      } else {
        summary.totalIncome += amount;
      }

      // Category breakdown
      const category = transaction.getCategoryString();
      if (!summary.categoryBreakdown[category]) {
        summary.categoryBreakdown[category] = { total: 0, count: 0 };
      }
      summary.categoryBreakdown[category].total += amount;
      summary.categoryBreakdown[category].count += 1;

      // Merchant totals
      const merchant = transaction.merchantName || 'Unknown';
      if (!merchantTotals[merchant]) {
        merchantTotals[merchant] = { total: 0, count: 0 };
      }
      merchantTotals[merchant].total += amount;
      merchantTotals[merchant].count += 1;
    });

    // Convert merchant totals to array and sort
    summary.topMerchants = Object.entries(merchantTotals)
      .map(([name, data]) => ({ name, ...data }))
      .sort((a, b) => b.total - a.total);

    return summary;
  }

  calculateTotalSpending(transactions, days = 30) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    return transactions
      .filter(t => new Date(t.date) >= cutoffDate && t.amount < 0)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);
  }

  calculateTotalIncome(transactions, days = 30) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);

    return transactions
      .filter(t => new Date(t.date) >= cutoffDate && t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0);
  }
}

module.exports = new AIAnalysisService();