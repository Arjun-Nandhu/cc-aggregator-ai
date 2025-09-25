const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Account = sequelize.define('Account', {
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
  plaidAccountId: {
    type: DataTypes.STRING,
    allowNull: false
  },
  institutionId: {
    type: DataTypes.STRING,
    allowNull: false
  },
  institutionName: {
    type: DataTypes.STRING,
    allowNull: false
  },
  accountName: {
    type: DataTypes.STRING,
    allowNull: false
  },
  accountType: {
    type: DataTypes.ENUM(
      'checking',
      'savings',
      'credit_card',
      'loan',
      'mortgage',
      'investment',
      'retirement',
      'other'
    ),
    allowNull: false
  },
  accountSubtype: {
    type: DataTypes.STRING,
    allowNull: true
  },
  accountNumberMasked: {
    type: DataTypes.STRING,
    allowNull: true
  },
  routingNumberMasked: {
    type: DataTypes.STRING,
    allowNull: true
  },
  balanceCurrent: {
    type: DataTypes.DECIMAL(15, 2),
    allowNull: true
  },
  balanceAvailable: {
    type: DataTypes.DECIMAL(15, 2),
    allowNull: true
  },
  balanceLimit: {
    type: DataTypes.DECIMAL(15, 2),
    allowNull: true
  },
  currencyCode: {
    type: DataTypes.STRING(3),
    defaultValue: 'USD'
  },
  isActive: {
    type: DataTypes.BOOLEAN,
    defaultValue: true
  },
  isConnected: {
    type: DataTypes.BOOLEAN,
    defaultValue: true
  },
  lastSyncAt: {
    type: DataTypes.DATE,
    allowNull: true
  },
  metadata: {
    type: DataTypes.JSON,
    defaultValue: {}
  }
}, {
  tableName: 'accounts',
  timestamps: true,
  indexes: [
    {
      fields: ['userId']
    },
    {
      fields: ['plaidAccountId']
    },
    {
      unique: true,
      fields: ['userId', 'plaidAccountId']
    },
    {
      fields: ['isActive']
    },
    {
      fields: ['isConnected']
    }
  ]
});

// Instance methods
Account.prototype.getDisplayName = function() {
  return `${this.institutionName} - ${this.accountName}`;
};

Account.prototype.getBalanceInfo = function() {
  return {
    current: this.balanceCurrent,
    available: this.balanceAvailable,
    limit: this.balanceLimit,
    currency: this.currencyCode
  };
};

// Static methods
Account.getByPlaidAccountId = async function(plaidAccountId) {
  return await this.findOne({ where: { plaidAccountId } });
};

module.exports = Account;