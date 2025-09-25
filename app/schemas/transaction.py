from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, date


class TransactionFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_ids: Optional[List[int]] = None
    category: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    merchant_name: Optional[str] = None


class TransactionCreate(BaseModel):
    plaid_transaction_id: str
    account_id: int
    amount: Decimal
    name: str
    date: date
    category: Optional[List[str]] = None
    merchant_name: Optional[str] = None
    pending: bool = False


class TransactionResponse(BaseModel):
    id: int
    plaid_transaction_id: str
    account_id: int
    amount: Decimal
    iso_currency_code: Optional[str] = None
    unofficial_currency_code: Optional[str] = None
    category: Optional[List[str]] = None
    category_id: Optional[str] = None
    merchant_name: Optional[str] = None
    name: str
    original_description: Optional[str] = None
    date: date
    authorized_date: Optional[date] = None
    pending: bool
    transaction_type: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    payment_meta: Optional[Dict[str, Any]] = None
    personal_finance_category: Optional[Dict[str, Any]] = None
    ai_category: Optional[str] = None
    ai_sentiment: Optional[str] = None
    ai_tags: Optional[List[str]] = None
    ai_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True