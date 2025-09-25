from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class AccountBalance(BaseModel):
    available: Optional[Decimal] = None
    current: Optional[Decimal] = None
    limit: Optional[Decimal] = None
    iso_currency_code: Optional[str] = None
    unofficial_currency_code: Optional[str] = None


class AccountResponse(BaseModel):
    id: int
    plaid_account_id: str
    name: str
    official_name: Optional[str] = None
    type: str
    subtype: str
    mask: Optional[str] = None
    balance: AccountBalance
    verification_status: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_account(cls, account):
        """Create AccountResponse from ORM Account model"""
        balance = AccountBalance(
            available=account.available_balance,
            current=account.current_balance,
            limit=account.limit_balance,
            iso_currency_code=account.iso_currency_code,
            unofficial_currency_code=account.unofficial_currency_code
        )
        
        return cls(
            id=account.id,
            plaid_account_id=account.plaid_account_id,
            name=account.name,
            official_name=account.official_name,
            type=account.type,
            subtype=account.subtype,
            mask=account.mask,
            balance=balance,
            verification_status=account.verification_status,
            created_at=account.created_at,
            updated_at=account.updated_at
        )