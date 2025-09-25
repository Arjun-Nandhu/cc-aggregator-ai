from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Institution schemas
class InstitutionBase(BaseModel):
    name: str
    plaid_institution_id: str


class InstitutionCreate(InstitutionBase):
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None


class Institution(InstitutionBase):
    id: int
    logo_url: Optional[str]
    primary_color: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Account schemas
class AccountBase(BaseModel):
    name: str
    type: str
    mask: str


class AccountCreate(AccountBase):
    institution_id: int
    plaid_account_id: str
    official_name: Optional[str] = None
    subtype: Optional[str] = None


class Account(AccountBase):
    id: int
    user_id: int
    institution_id: int
    plaid_account_id: str
    official_name: Optional[str]
    subtype: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Transaction schemas
class TransactionBase(BaseModel):
    amount: float
    date: datetime
    name: str
    is_pending: bool = False


class TransactionCreate(TransactionBase):
    account_id: int
    plaid_transaction_id: str
    merchant_name: Optional[str] = None
    category: Optional[List[str]] = None
    subcategory: Optional[List[str]] = None
    account_owner: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class Transaction(TransactionBase):
    id: int
    user_id: int
    account_id: int
    plaid_transaction_id: str
    merchant_name: Optional[str]
    category: Optional[List[str]]
    subcategory: Optional[List[str]]
    account_owner: Optional[str]
    raw_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# AI Analysis schemas
class AIAnalysisBase(BaseModel):
    analysis_type: str
    results: Dict[str, Any]
    confidence_score: Optional[float] = None


class AIAnalysisCreate(AIAnalysisBase):
    pass


class AIAnalysis(AIAnalysisBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Plaid schemas
class PlaidLinkToken(BaseModel):
    link_token: str
    expiration: datetime


class PlaidPublicToken(BaseModel):
    public_token: str
    institution_id: str
    accounts: List[Dict[str, Any]]


# Analysis request schemas
class AnalysisRequest(BaseModel):
    analysis_type: str
    date_range: Optional[Dict[str, datetime]] = None
    account_ids: Optional[List[int]] = None