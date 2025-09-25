import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalance,
  Receipt,
  ShowChart,
  Refresh,
} from '@mui/icons-material';
import { accountsAPI, transactionsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface Account {
  id: string;
  accountName: string;
  institutionName: string;
  accountType: string;
  balanceCurrent: number;
  balanceAvailable: number;
  currencyCode: string;
  isActive: boolean;
  isConnected: boolean;
}

interface Transaction {
  id: string;
  amount: number;
  merchantName: string;
  category: string[];
  date: string;
  transactionType: string;
  account: {
    accountName: string;
    institutionName: string;
  };
}

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [accountsResponse, transactionsResponse] = await Promise.all([
        accountsAPI.getAccounts(),
        transactionsAPI.getTransactions({ limit: 10 }),
      ]);

      setAccounts(accountsResponse.data.accounts);
      setRecentTransactions(transactionsResponse.data.transactions);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncAll = async () => {
    try {
      setSyncing(true);
      await transactionsAPI.syncTransactions();
      await loadDashboardData();
    } catch (error) {
      console.error('Error syncing data:', error);
    } finally {
      setSyncing(false);
    }
  };

  const totalBalance = accounts.reduce((sum, account) => sum + (account.balanceCurrent || 0), 0);
  const monthlySpending = recentTransactions
    .filter(t => t.transactionType === 'debit' && new Date(t.date) >= new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading dashboard...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Welcome back, {user?.firstName}!
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleSyncAll}
          disabled={syncing}
        >
          {syncing ? 'Syncing...' : 'Sync All'}
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AccountBalance color="primary" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Balance
                  </Typography>
                  <Typography variant="h4">
                    ${totalBalance.toFixed(2)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingDown color="error" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Monthly Spending
                  </Typography>
                  <Typography variant="h4">
                    ${monthlySpending.toFixed(2)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <ShowChart color="success" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Connected Accounts
                  </Typography>
                  <Typography variant="h4">
                    {accounts.filter(a => a.isConnected).length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Accounts Overview */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Connected Accounts
            </Typography>
            {accounts.length === 0 ? (
              <Typography color="textSecondary">
                No accounts connected yet. Connect your first account to get started.
              </Typography>
            ) : (
              <List>
                {accounts.slice(0, 5).map((account) => (
                  <ListItem key={account.id}>
                    <ListItemAvatar>
                      <Avatar>
                        <AccountBalance />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={account.accountName}
                      secondary={`${account.institutionName} • ${account.accountType}`}
                    />
                    <Typography variant="body2" color="textSecondary">
                      ${account.balanceCurrent?.toFixed(2) || '0.00'}
                    </Typography>
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Recent Transactions */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Transactions
            </Typography>
            {recentTransactions.length === 0 ? (
              <Typography color="textSecondary">
                No transactions yet. Connect your accounts to see transaction data.
              </Typography>
            ) : (
              <List>
                {recentTransactions.slice(0, 5).map((transaction, index) => (
                  <React.Fragment key={transaction.id}>
                    <ListItem>
                      <ListItemAvatar>
                        <Avatar>
                          <Receipt />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={transaction.merchantName || 'Unknown'}
                        secondary={
                          <Box>
                            <Typography variant="body2" component="span">
                              {transaction.account.accountName}
                            </Typography>
                            <Typography variant="caption" component="div" color="textSecondary">
                              {new Date(transaction.date).toLocaleDateString()}
                            </Typography>
                            {transaction.category && transaction.category.length > 0 && (
                              <Chip
                                label={transaction.category[0]}
                                size="small"
                                sx={{ mt: 0.5 }}
                              />
                            )}
                          </Box>
                        }
                      />
                      <Typography
                        variant="body2"
                        color={transaction.amount >= 0 ? 'success.main' : 'error.main'}
                      >
                        {transaction.amount >= 0 ? '+' : ''}${Math.abs(transaction.amount).toFixed(2)}
                      </Typography>
                    </ListItem>
                    {index < recentTransactions.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;