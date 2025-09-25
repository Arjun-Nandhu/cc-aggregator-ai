from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from decimal import Decimal

from app.models.account import Account
from app.models.institution import Institution
from app.models.plaid_item import PlaidItem
from app.schemas.account import AccountResponse


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def create_account(self, account_data: Dict[str, Any], user_id: int, plaid_item_id: int, institution_id: int) -> Account:
        """Create a new account from Plaid data"""
        account = Account(
            plaid_account_id=account_data["account_id"],
            user_id=user_id,
            institution_id=institution_id,
            plaid_item_id=plaid_item_id,
            name=account_data["name"],
            official_name=account_data.get("official_name"),
            type=account_data["type"],
            subtype=account_data["subtype"],
            mask=account_data.get("mask"),
            available_balance=account_data["balances"].get("available"),
            current_balance=account_data["balances"].get("current"),
            limit_balance=account_data["balances"].get("limit"),
            iso_currency_code=account_data["balances"].get("iso_currency_code"),
            unofficial_currency_code=account_data["balances"].get("unofficial_currency_code"),
            verification_status=account_data.get("verification_status"),
            persistent_account_id=account_data.get("persistent_account_id")
        )
        
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account_by_plaid_id(self, plaid_account_id: str) -> Optional[Account]:
        """Get account by Plaid account ID"""
        return self.db.query(Account).filter(Account.plaid_account_id == plaid_account_id).first()

    def get_accounts_by_user(self, user_id: int) -> List[Account]:
        """Get all accounts for a user"""
        return self.db.query(Account).filter(Account.user_id == user_id).all()

    def get_accounts_by_institution(self, user_id: int, institution_id: int) -> List[Account]:
        """Get accounts by user and institution"""
        return self.db.query(Account).filter(
            and_(Account.user_id == user_id, Account.institution_id == institution_id)
        ).all()

    def get_account_by_id(self, account_id: int, user_id: int) -> Optional[Account]:
        """Get account by ID and user ID"""
        return self.db.query(Account).filter(
            and_(Account.id == account_id, Account.user_id == user_id)
        ).first()

    def update_account_balances(self, plaid_account_id: str, balances: Dict[str, Any]) -> Account:
        """Update account balances"""
        account = self.get_account_by_plaid_id(plaid_account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        account.available_balance = balances.get("available")
        account.current_balance = balances.get("current")
        account.limit_balance = balances.get("limit")
        account.iso_currency_code = balances.get("iso_currency_code")
        account.unofficial_currency_code = balances.get("unofficial_currency_code")
        
        self.db.commit()
        self.db.refresh(account)
        return account

    def delete_account(self, account_id: int, user_id: int) -> bool:
        """Delete an account"""
        account = self.get_account_by_id(account_id, user_id)
        if not account:
            return False
        
        self.db.delete(account)
        self.db.commit()
        return True

    def get_account_summary(self, user_id: int) -> Dict[str, Any]:
        """Get account summary for a user"""
        accounts = self.get_accounts_by_user(user_id)
        
        total_checking = Decimal('0')
        total_savings = Decimal('0')
        total_credit = Decimal('0')
        total_investment = Decimal('0')
        
        account_counts = {
            'checking': 0,
            'savings': 0,
            'credit': 0,
            'investment': 0,
            'other': 0
        }
        
        for account in accounts:
            if account.current_balance:
                if account.type == 'depository':
                    if account.subtype == 'checking':
                        total_checking += account.current_balance
                        account_counts['checking'] += 1
                    elif account.subtype == 'savings':
                        total_savings += account.current_balance
                        account_counts['savings'] += 1
                elif account.type == 'credit':
                    total_credit += account.current_balance
                    account_counts['credit'] += 1
                elif account.type == 'investment':
                    total_investment += account.current_balance
                    account_counts['investment'] += 1
                else:
                    account_counts['other'] += 1
        
        return {
            'total_accounts': len(accounts),
            'account_counts': account_counts,
            'balances': {
                'total_checking': total_checking,
                'total_savings': total_savings,
                'total_credit': total_credit,
                'total_investment': total_investment,
                'net_worth': total_checking + total_savings + total_investment - abs(total_credit)
            }
        }

    def sync_accounts_from_plaid(self, accounts_data: List[Dict[str, Any]], user_id: int, plaid_item_id: int, institution_id: int):
        """Sync accounts from Plaid data"""
        for account_data in accounts_data:
            existing_account = self.get_account_by_plaid_id(account_data["account_id"])
            
            if existing_account:
                # Update existing account balances
                self.update_account_balances(account_data["account_id"], account_data["balances"])
            else:
                # Create new account
                self.create_account(account_data, user_id, plaid_item_id, institution_id)