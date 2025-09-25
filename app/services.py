from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from app.models import User, Account, Transaction, Institution, AIAnalysis
from app.plaid_service import PlaidService
from app.schemas import TransactionCreate, AccountCreate, InstitutionCreate


class FinancialDataService:
    """Service for managing financial data operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_institution(self, institution_data: Dict[str, Any]) -> Institution:
        """Create or get institution"""
        institution = self.db.query(Institution).filter(
            Institution.plaid_institution_id == institution_data['institution_id']
        ).first()
        
        if not institution:
            institution = Institution(
                name=institution_data['name'],
                plaid_institution_id=institution_data['institution_id'],
                logo_url=institution_data.get('logo_url'),
                primary_color=institution_data.get('primary_color')
            )
            self.db.add(institution)
            self.db.commit()
            self.db.refresh(institution)
        
        return institution
    
    def create_accounts(self, user_id: int, accounts_data: List[Dict[str, Any]], institution_id: int) -> List[Account]:
        """Create accounts for a user"""
        created_accounts = []
        
        for account_data in accounts_data:
            # Check if account already exists
            existing_account = self.db.query(Account).filter(
                Account.plaid_account_id == account_data['account_id']
            ).first()
            
            if not existing_account:
                account = Account(
                    user_id=user_id,
                    institution_id=institution_id,
                    plaid_account_id=account_data['account_id'],
                    name=account_data['name'],
                    official_name=account_data.get('official_name'),
                    type=account_data['type'],
                    subtype=account_data.get('subtype'),
                    mask=account_data.get('mask', '')
                )
                self.db.add(account)
                created_accounts.append(account)
        
        self.db.commit()
        return created_accounts
    
    def create_transactions(self, user_id: int, transactions_data: List[Dict[str, Any]]) -> List[Transaction]:
        """Create transactions for a user"""
        created_transactions = []
        
        for transaction_data in transactions_data:
            # Check if transaction already exists
            existing_transaction = self.db.query(Transaction).filter(
                Transaction.plaid_transaction_id == transaction_data['transaction_id']
            ).first()
            
            if not existing_transaction:
                # Find account by plaid_account_id
                account = self.db.query(Account).filter(
                    Account.plaid_account_id == transaction_data['account_id']
                ).first()
                
                if account:
                    transaction = Transaction(
                        user_id=user_id,
                        account_id=account.id,
                        plaid_transaction_id=transaction_data['transaction_id'],
                        amount=transaction_data['amount'],
                        date=datetime.fromisoformat(transaction_data['date'].replace('Z', '+00:00')),
                        name=transaction_data['name'],
                        merchant_name=transaction_data.get('merchant_name'),
                        category=transaction_data.get('category'),
                        subcategory=transaction_data.get('subcategory'),
                        account_owner=transaction_data.get('account_owner'),
                        is_pending=transaction_data.get('pending', False),
                        raw_data=transaction_data
                    )
                    self.db.add(transaction)
                    created_transactions.append(transaction)
        
        self.db.commit()
        return created_transactions
    
    def sync_user_data(self, user_id: int, access_token: str) -> Dict[str, Any]:
        """Sync all data for a user from Plaid"""
        try:
            # Get accounts
            accounts_data = PlaidService.get_accounts(access_token)
            
            # Get transactions (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            transactions_data = PlaidService.get_transactions(access_token, start_date, end_date)
            
            # Process accounts
            created_accounts = []
            for account_data in accounts_data:
                # Get institution info
                institution_data = PlaidService.get_institution_by_id(account_data.get('institution_id', ''))
                institution = self.create_institution(institution_data)
                
                # Create account
                account = Account(
                    user_id=user_id,
                    institution_id=institution.id,
                    plaid_account_id=account_data['account_id'],
                    name=account_data['name'],
                    official_name=account_data.get('official_name'),
                    type=account_data['type'],
                    subtype=account_data.get('subtype'),
                    mask=account_data.get('mask', '')
                )
                self.db.add(account)
                created_accounts.append(account)
            
            self.db.commit()
            
            # Process transactions
            created_transactions = []
            for transaction_data in transactions_data:
                # Find account
                account = self.db.query(Account).filter(
                    Account.plaid_account_id == transaction_data['account_id']
                ).first()
                
                if account:
                    transaction = Transaction(
                        user_id=user_id,
                        account_id=account.id,
                        plaid_transaction_id=transaction_data['transaction_id'],
                        amount=transaction_data['amount'],
                        date=datetime.fromisoformat(transaction_data['date'].replace('Z', '+00:00')),
                        name=transaction_data['name'],
                        merchant_name=transaction_data.get('merchant_name'),
                        category=transaction_data.get('category'),
                        subcategory=transaction_data.get('subcategory'),
                        account_owner=transaction_data.get('account_owner'),
                        is_pending=transaction_data.get('pending', False),
                        raw_data=transaction_data
                    )
                    self.db.add(transaction)
                    created_transactions.append(transaction)
            
            self.db.commit()
            
            return {
                'accounts_created': len(created_accounts),
                'transactions_created': len(created_transactions),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }


class AIAnalysisService:
    """Service for AI-powered financial analysis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_spending_patterns(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Analyze user's spending patterns"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0  # Only spending transactions
        ).all()
        
        if not transactions:
            return {'error': 'No transactions found for analysis'}
        
        # Convert to DataFrame for analysis
        data = []
        for t in transactions:
            data.append({
                'amount': abs(t.amount),
                'date': t.date,
                'category': t.category[0] if t.category else 'Other',
                'merchant': t.merchant_name or t.name
            })
        
        df = pd.DataFrame(data)
        
        # Basic analysis
        total_spending = df['amount'].sum()
        avg_daily_spending = df.groupby(df['date'].dt.date)['amount'].sum().mean()
        
        # Category analysis
        category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        # Monthly spending trend
        monthly_spending = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
        
        # Spending patterns by day of week
        df['day_of_week'] = df['date'].dt.day_name()
        daily_patterns = df.groupby('day_of_week')['amount'].sum()
        
        # Top merchants
        top_merchants = df.groupby('merchant')['amount'].sum().sort_values(ascending=False).head(10)
        
        analysis_result = {
            'total_spending': float(total_spending),
            'avg_daily_spending': float(avg_daily_spending),
            'category_breakdown': category_spending.to_dict(),
            'monthly_trend': {str(k): float(v) for k, v in monthly_spending.items()},
            'daily_patterns': daily_patterns.to_dict(),
            'top_merchants': top_merchants.to_dict(),
            'transaction_count': len(transactions),
            'analysis_date': datetime.now().isoformat()
        }
        
        # Save analysis to database
        ai_analysis = AIAnalysis(
            user_id=user_id,
            analysis_type='spending_patterns',
            results=analysis_result,
            confidence_score=0.85
        )
        self.db.add(ai_analysis)
        self.db.commit()
        
        return analysis_result
    
    def detect_anomalies(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Detect unusual spending patterns"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0
        ).all()
        
        if len(transactions) < 10:
            return {'error': 'Insufficient data for anomaly detection'}
        
        # Convert to DataFrame
        data = []
        for t in transactions:
            data.append({
                'amount': abs(t.amount),
                'date': t.date,
                'category': t.category[0] if t.category else 'Other'
            })
        
        df = pd.DataFrame(data)
        
        # Calculate spending by category
        category_spending = df.groupby('category')['amount'].sum()
        
        # Detect anomalies using statistical methods
        anomalies = []
        
        # Z-score based anomaly detection
        for category in category_spending.index:
            category_data = df[df['category'] == category]['amount']
            if len(category_data) > 1:
                z_scores = np.abs((category_data - category_data.mean()) / category_data.std())
                anomaly_indices = z_scores[z_scores > 2].index
                
                for idx in anomaly_indices:
                    transaction = transactions[idx]
                    anomalies.append({
                        'transaction_id': transaction.id,
                        'amount': abs(transaction.amount),
                        'date': transaction.date.isoformat(),
                        'category': category,
                        'anomaly_score': float(z_scores[idx]),
                        'reason': 'Statistical outlier'
                    })
        
        # Large transaction detection
        large_transactions = df[df['amount'] > df['amount'].quantile(0.95)]
        for idx in large_transactions.index:
            transaction = transactions[idx]
            anomalies.append({
                'transaction_id': transaction.id,
                'amount': abs(transaction.amount),
                'date': transaction.date.isoformat(),
                'category': transaction.category[0] if transaction.category else 'Other',
                'anomaly_score': 1.0,
                'reason': 'Large transaction'
            })
        
        analysis_result = {
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies,
            'analysis_date': datetime.now().isoformat()
        }
        
        # Save analysis
        ai_analysis = AIAnalysis(
            user_id=user_id,
            analysis_type='anomaly_detection',
            results=analysis_result,
            confidence_score=0.75
        )
        self.db.add(ai_analysis)
        self.db.commit()
        
        return analysis_result