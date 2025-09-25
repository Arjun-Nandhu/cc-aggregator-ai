const { DataTypes, Op } = require('sequelize');
const sequelize = require('../config/database');

const Transaction = sequelize.define('Transaction', {
  id: {
    type: DataTypes.UUID,
    defaultValue: DataTypes.UUIDV4,
    primaryKey: true
  },
  userId: {
    type: DataTypes.UUID,
    allowNull: false,
    references: {
      model: 'users',
      key: 'id'
    }
  },
  accountId: {
    type: DataTypes.UUID,
    allowNull: false,
    references: {
      model: 'accounts',
      key: 'id'
    }
  },
  plaidTransactionId: {
    type: DataTypes.STRING,
    allowNull: false
  },
  amount: {
    type: DataTypes.DECIMAL(15, 2),
    allowNull: false
  },
  currencyCode: {
    type: DataTypes.STRING(3),
    defaultValue: 'USD'
  },
  date: {
    type: DataTypes.DATEONLY,
    allowNull: false
  },
  datetime: {
    type: DataTypes.DATE,
    allowNull: true
  },
  merchantName: {
    type: DataTypes.STRING,
    allowNull: true
  },
  merchantCategory: {
    type: DataTypes.STRING,
    allowNull: true
  },
  category: {
    type: DataTypes.JSON,
    allowNull: true,
    defaultValue: []
  },
  subcategory: {
    type: DataTypes.JSON,
    allowNull: true,
    defaultValue: []
  },
  description: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  location: {
    type: DataTypes.JSON,
    allowNull: true,
    defaultValue: {}
  },
  paymentMethod: {
    type: DataTypes.STRING,
    allowNull: true
  },
  paymentChannel: {
    type: DataTypes.ENUM('online', 'in store', 'other'),
    allowNull: true
  },
  transactionType: {
    type: DataTypes.ENUM('debit', 'credit', 'transfer', 'fee', 'interest', 'other'),
    allowNull: false
  },
  pending: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  },
  isRecurring: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  },
  recurrencePattern: {
    type: DataTypes.JSON,
    allowNull: true,
    defaultValue: {}
  },
  tags: {
    type: DataTypes.JSON,
    allowNull: true,
    defaultValue: []
  },
  notes: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  aiAnalysis: {
    type: DataTypes.JSON,
    allowNull: true,
    defaultValue: {}
  },
  confidence: {
    type: DataTypes.DECIMAL(3, 2),
    allowNull: true,
    validate: {
      min: 0,
      max: 1
    }
  }
}, {
  tableName: 'transactions',
  timestamps: true,
  indexes: [
    {
      fields: ['userId']
    },
    {
      fields: ['accountId']
    },
    {
      fields: ['plaidTransactionId']
    },
    {
      unique: true,
      fields: ['userId', 'plaidTransactionId']
    },
    {
      fields: ['date']
    },
    {
      fields: ['merchantName']
    },
    {
      fields: ['category']
    },
    {
      fields: ['transactionType']
    },
    {
      fields: ['pending']
    }
  ]
});

// Instance methods
Transaction.prototype.isIncome = function() {
  return this.amount > 0;
};

Transaction.prototype.isExpense = function() {
  return this.amount < 0;
};

Transaction.prototype.getAbsoluteAmount = function() {
  return Math.abs(this.amount);
};

Transaction.prototype.getFormattedAmount = function() {
  const absAmount = this.getAbsoluteAmount();
  const sign = this.amount >= 0 ? '+' : '-';
  return `${sign}$${absAmount.toFixed(2)}`;
};

Transaction.prototype.getCategoryString = function() {
  if (this.category && this.category.length > 0) {
    return this.category.join(' > ');
  }
  return 'Uncategorized';
};

// Static methods
Transaction.getByPlaidTransactionId = async function(plaidTransactionId) {
  return await this.findOne({ where: { plaidTransactionId } });
};

Transaction.getUserTransactionsByDateRange = async function(userId, startDate, endDate) {
  return await this.findAll({
    where: {
      userId,
      date: {
        [Op.between]: [startDate, endDate]
      }
    },
    order: [['date', 'DESC'], ['datetime', 'DESC']]
  });
};

Transaction.getTransactionsByCategory = async function(userId, category, limit = 50) {
  return await this.findAll({
    where: {
      userId,
      category: {
        [Op.contains]: [category]
      }
    },
    limit,
    order: [['date', 'DESC']]
  });
};

module.exports = Transaction;