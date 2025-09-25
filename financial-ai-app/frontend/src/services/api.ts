import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (userData: RegisterData) => api.post('/auth/register', userData),
  login: (credentials: LoginCredentials) => api.post('/auth/login', credentials),
  getProfile: () => api.get('/auth/me'),
  updateProfile: (profileData: ProfileUpdateData) => api.put('/auth/me', profileData),
  changePassword: (passwordData: ChangePasswordData) => api.put('/auth/change-password', passwordData),
  logout: () => api.post('/auth/logout'),
};

// Accounts API
export const accountsAPI = {
  getAccounts: () => api.get('/accounts'),
  getAccount: (accountId: string) => api.get(`/accounts/${accountId}`),
  createLinkToken: () => api.post('/accounts/link-token'),
  exchangeToken: (publicToken: string) => api.post('/accounts/exchange-token', { publicToken }),
  syncAccount: (accountId: string) => api.post(`/accounts/${accountId}/sync`),
  disconnectAccount: (accountId: string) => api.delete(`/accounts/${accountId}`),
};

// Transactions API
export const transactionsAPI = {
  getTransactions: (params?: TransactionFilters) => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return api.get(`/transactions?${queryParams.toString()}`);
  },
  getTransaction: (transactionId: string) => api.get(`/transactions/${transactionId}`),
  syncTransactions: (syncData?: SyncData) => api.post('/transactions/sync', syncData),
  analyzeTransaction: (transactionId: string) => api.post(`/transactions/${transactionId}/analyze`),
  updateTransaction: (transactionId: string, updateData: TransactionUpdateData) =>
    api.put(`/transactions/${transactionId}`, updateData),
  deleteTransaction: (transactionId: string) => api.delete(`/transactions/${transactionId}`),
};

// Type definitions
export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phoneNumber?: string;
  dateOfBirth?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface ProfileUpdateData {
  firstName?: string;
  lastName?: string;
  phoneNumber?: string;
  dateOfBirth?: string;
  preferences?: UserPreferences;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
}

export interface UserPreferences {
  notifications?: {
    email: boolean;
    sms: boolean;
    push: boolean;
  };
  analysisFrequency?: string;
  currency?: string;
  timezone?: string;
}

export interface TransactionFilters {
  startDate?: string;
  endDate?: string;
  accountId?: string;
  category?: string;
  merchant?: string;
  type?: string;
  limit?: number;
  offset?: number;
  sortBy?: string;
  sortOrder?: 'ASC' | 'DESC';
}

export interface SyncData {
  accountId?: string;
  startDate?: string;
  endDate?: string;
}

export interface TransactionUpdateData {
  notes?: string;
  tags?: string[];
  category?: string[];
}

export default api;