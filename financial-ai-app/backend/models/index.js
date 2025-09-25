const sequelize = require('../config/database');
const User = require('./User');
const Account = require('./Account');
const Transaction = require('./Transaction');

// Define associations
User.hasMany(Account, {
  foreignKey: 'userId',
  as: 'accounts',
  onDelete: 'CASCADE'
});

Account.belongsTo(User, {
  foreignKey: 'userId',
  as: 'user'
});

User.hasMany(Transaction, {
  foreignKey: 'userId',
  as: 'transactions',
  onDelete: 'CASCADE'
});

Account.hasMany(Transaction, {
  foreignKey: 'accountId',
  as: 'transactions',
  onDelete: 'CASCADE'
});

Transaction.belongsTo(User, {
  foreignKey: 'userId',
  as: 'user'
});

Transaction.belongsTo(Account, {
  foreignKey: 'accountId',
  as: 'account'
});

// Sync database (create tables)
const syncDatabase = async (force = false) => {
  try {
    await sequelize.sync({ force });
    console.log('✅ Database synchronized successfully');
  } catch (error) {
    console.error('❌ Error synchronizing database:', error);
    throw error;
  }
};

// Export models and utilities
module.exports = {
  sequelize,
  User,
  Account,
  Transaction,
  syncDatabase,
  Op: require('sequelize').Op
};