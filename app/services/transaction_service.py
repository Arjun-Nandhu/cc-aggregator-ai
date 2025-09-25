from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.transaction import TransactionFilter, TransactionResponse


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, transaction_data: Dict[str, Any], user_id: int, account_id: int) -> Transaction:
        """Create a new transaction from Plaid data"""
        transaction = Transaction(
            plaid_transaction_id=transaction_data["transaction_id"],
            user_id=user_id,
            account_id=account_id,
            amount=Decimal(str(transaction_data["amount"])),
            iso_currency_code=transaction_data.get("iso_currency_code"),
            unofficial_currency_code=transaction_data.get("unofficial_currency_code"),
            category=transaction_data.get("category", []),
            category_id=transaction_data.get("category_id"),
            merchant_name=transaction_data.get("merchant_name"),
            name=transaction_data["name"],
            original_description=transaction_data.get("original_description"),
            date=datetime.fromisoformat(transaction_data["date"]).date(),
            authorized_date=datetime.fromisoformat(transaction_data["authorized_date"]).date() if transaction_data.get("authorized_date") else None,
            authorized_datetime=datetime.fromisoformat(transaction_data["authorized_datetime"]) if transaction_data.get("authorized_datetime") else None,
            datetime=datetime.fromisoformat(transaction_data["datetime"]) if transaction_data.get("datetime") else None,
            pending=transaction_data.get("pending", False),
            pending_transaction_id=transaction_data.get("pending_transaction_id"),
            account_owner=transaction_data.get("account_owner"),
            transaction_type=transaction_data.get("transaction_type"),
            transaction_code=transaction_data.get("transaction_code"),
            location=transaction_data.get("location", {}),
            payment_meta=transaction_data.get("payment_meta", {}),
            personal_finance_category=transaction_data.get("personal_finance_category", {})
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_transaction_by_plaid_id(self, plaid_transaction_id: str) -> Optional[Transaction]:
        """Get transaction by Plaid transaction ID"""
        return self.db.query(Transaction).filter(Transaction.plaid_transaction_id == plaid_transaction_id).first()

    def get_transactions_by_user(
        self, 
        user_id: int, 
        filters: Optional[TransactionFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transactions for a user with optional filtering"""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if filters:
            if filters.start_date:
                query = query.filter(Transaction.date >= filters.start_date)
            if filters.end_date:
                query = query.filter(Transaction.date <= filters.end_date)
            if filters.account_ids:
                query = query.filter(Transaction.account_id.in_(filters.account_ids))
            if filters.category:
                query = query.filter(Transaction.category.contains([filters.category]))
            if filters.min_amount:
                query = query.filter(Transaction.amount >= filters.min_amount)
            if filters.max_amount:
                query = query.filter(Transaction.amount <= filters.max_amount)
            if filters.merchant_name:
                query = query.filter(Transaction.merchant_name.ilike(f"%{filters.merchant_name}%"))
        
        return query.order_by(desc(Transaction.date)).offset(offset).limit(limit).all()

    def get_transactions_by_account(self, account_id: int, user_id: int) -> List[Transaction]:
        """Get transactions for a specific account"""
        return self.db.query(Transaction).filter(
            and_(Transaction.account_id == account_id, Transaction.user_id == user_id)
        ).order_by(desc(Transaction.date)).all()

    def update_transaction(self, transaction_id: int, user_id: int, updates: Dict[str, Any]) -> Transaction:
        """Update transaction with new data"""
        transaction = self.db.query(Transaction).filter(
            and_(Transaction.id == transaction_id, Transaction.user_id == user_id)
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        for field, value in updates.items():
            if hasattr(transaction, field):
                setattr(transaction, field, value)
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def delete_transaction(self, transaction_id: int, user_id: int) -> bool:
        """Delete a transaction"""
        transaction = self.db.query(Transaction).filter(
            and_(Transaction.id == transaction_id, Transaction.user_id == user_id)
        ).first()
        
        if not transaction:
            return False
        
        self.db.delete(transaction)
        self.db.commit()
        return True

    def get_transaction_analytics(self, user_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get transaction analytics for a user within date range"""
        transactions = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        ).all()
        
        total_income = Decimal('0')
        total_expenses = Decimal('0')
        category_spending = {}
        merchant_spending = {}
        monthly_trends = {}
        
        for transaction in transactions:
            amount = transaction.amount
            
            # Income vs Expenses (negative amounts are typically income in Plaid)
            if amount < 0:
                total_income += abs(amount)
            else:
                total_expenses += amount
            
            # Category analysis
            if transaction.category:
                primary_category = transaction.category[0] if transaction.category else "Other"
                category_spending[primary_category] = category_spending.get(primary_category, Decimal('0')) + amount
            
            # Merchant analysis
            if transaction.merchant_name:
                merchant_spending[transaction.merchant_name] = merchant_spending.get(transaction.merchant_name, Decimal('0')) + amount
            
            # Monthly trends
            month_key = transaction.date.strftime("%Y-%m")
            if month_key not in monthly_trends:
                monthly_trends[month_key] = {'income': Decimal('0'), 'expenses': Decimal('0')}
            
            if amount < 0:
                monthly_trends[month_key]['income'] += abs(amount)
            else:
                monthly_trends[month_key]['expenses'] += amount
        
        # Sort categories and merchants by spending
        top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:10]
        top_merchants = sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'summary': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_income': total_income - total_expenses,
                'transaction_count': len(transactions)
            },
            'top_categories': [{'category': cat, 'amount': float(amount)} for cat, amount in top_categories],
            'top_merchants': [{'merchant': merchant, 'amount': float(amount)} for merchant, amount in top_merchants],
            'monthly_trends': {
                month: {
                    'income': float(data['income']),
                    'expenses': float(data['expenses']),
                    'net': float(data['income'] - data['expenses'])
                }
                for month, data in monthly_trends.items()
            }
        }

    def sync_transactions_from_plaid(self, transactions_data: List[Dict[str, Any]], user_id: int):
        """Sync transactions from Plaid data"""
        account_cache = {}
        
        for transaction_data in transactions_data:
            plaid_account_id = transaction_data["account_id"]
            
            # Get account ID from cache or database
            if plaid_account_id not in account_cache:
                account = self.db.query(Account).filter(Account.plaid_account_id == plaid_account_id).first()
                if not account:
                    continue  # Skip if account not found
                account_cache[plaid_account_id] = account.id
            
            account_id = account_cache[plaid_account_id]
            
            # Check if transaction already exists
            existing_transaction = self.get_transaction_by_plaid_id(transaction_data["transaction_id"])
            
            if existing_transaction:
                # Update existing transaction
                updates = {
                    'amount': Decimal(str(transaction_data["amount"])),
                    'name': transaction_data["name"],
                    'merchant_name': transaction_data.get("merchant_name"),
                    'category': transaction_data.get("category", []),
                    'pending': transaction_data.get("pending", False)
                }
                self.update_transaction(existing_transaction.id, user_id, updates)
            else:
                # Create new transaction
                self.create_transaction(transaction_data, user_id, account_id)

    def remove_transactions_by_plaid_ids(self, plaid_transaction_ids: List[str], user_id: int):
        """Remove transactions by Plaid transaction IDs"""
        self.db.query(Transaction).filter(
            and_(
                Transaction.plaid_transaction_id.in_(plaid_transaction_ids),
                Transaction.user_id == user_id
            )
        ).delete(synchronize_session=False)
        self.db.commit()