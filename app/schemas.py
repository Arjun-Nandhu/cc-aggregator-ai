from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Institution Schemas
class InstitutionBase(BaseModel):
    name: str
    logo: Optional[str] = None
    primary_color: Optional[str] = None
    url: Optional[str] = None


class InstitutionResponse(InstitutionBase):
    id: int
    plaid_institution_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Account Schemas
class AccountBase(BaseModel):
    name: str
    type: str
    subtype: Optional[str] = None


class AccountCreate(AccountBase):
    plaid_account_id: str
    institution_id: int
    official_name: Optional[str] = None
    mask: Optional[str] = None
    balance_available: Optional[float] = None
    balance_current: Optional[float] = None
    balance_limit: Optional[float] = None
    currency_code: str = "USD"


class AccountResponse(AccountBase):
    id: int
    user_id: int
    plaid_account_id: str
    institution_id: int
    official_name: Optional[str]
    mask: Optional[str]
    balance_available: Optional[float]
    balance_current: Optional[float]
    balance_limit: Optional[float]
    currency_code: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    amount: float
    date: datetime
    name: str


class TransactionCreate(TransactionBase):
    account_id: int
    plaid_transaction_id: str
    merchant_name: Optional[str] = None
    category: Optional[List[str]] = None
    subcategory: Optional[List[str]] = None
    account_owner: Optional[str] = None
    pending: bool = False
    iso_currency_code: str = "USD"
    unofficial_currency_code: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    payment_meta: Optional[Dict[str, Any]] = None


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    account_id: int
    plaid_transaction_id: str
    merchant_name: Optional[str]
    category: Optional[List[str]]
    subcategory: Optional[List[str]]
    account_owner: Optional[str]
    pending: bool
    iso_currency_code: str
    unofficial_currency_code: Optional[str]
    location: Optional[Dict[str, Any]]
    payment_meta: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# AI Analysis Schemas
class AIAnalysisBase(BaseModel):
    analysis_type: str
    data: Dict[str, Any]
    insights: Optional[str] = None
    confidence_score: Optional[float] = None


class AIAnalysisCreate(AIAnalysisBase):
    pass


class AIAnalysisResponse(AIAnalysisBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Plaid Link Token Schema
class LinkTokenResponse(BaseModel):
    link_token: str
    expiration: str


# Plaid Exchange Token Schema
class ExchangeTokenRequest(BaseModel):
    public_token: str


class ExchangeTokenResponse(BaseModel):
    access_token: str
    item_id: str
    success: bool