from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class PlaidLinkTokenRequest(BaseModel):
    user_id: int
    institution_id: Optional[str] = None
    webhook_url: Optional[str] = None


class PlaidExchangeRequest(BaseModel):
    public_token: str
    institution_id: Optional[str] = None
    webhook_url: Optional[str] = None


class PlaidLinkResponse(BaseModel):
    link_token: str
    expiration: str
    request_id: str


class PlaidItemResponse(BaseModel):
    item_id: str
    access_token: str
    institution_id: str
    webhook_url: Optional[str] = None


class PlaidAccountResponse(BaseModel):
    account_id: str
    name: str
    official_name: Optional[str] = None
    type: str
    subtype: str
    mask: Optional[str] = None
    balances: Dict[str, Any]


class PlaidTransactionResponse(BaseModel):
    transaction_id: str
    account_id: str
    amount: float
    name: str
    merchant_name: Optional[str] = None
    category: Optional[List[str]] = None
    date: str
    pending: bool
    location: Optional[Dict[str, Any]] = None