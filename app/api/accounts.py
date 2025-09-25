from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.utils.auth import get_current_active_user
from app.services.account_service import AccountService
from app.schemas.account import AccountResponse
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all accounts for the current user"""
    account_service = AccountService(db)
    accounts = account_service.get_accounts_by_user(current_user.id)
    
    return [AccountResponse.from_orm_account(account) for account in accounts]


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific account by ID"""
    account_service = AccountService(db)
    account = account_service.get_account_by_id(account_id, current_user.id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return AccountResponse.from_orm_account(account)


@router.get("/summary/overview")
async def get_account_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get account summary and overview for the current user"""
    account_service = AccountService(db)
    summary = account_service.get_account_summary(current_user.id)
    
    return summary


@router.get("/institution/{institution_id}", response_model=List[AccountResponse])
async def get_accounts_by_institution(
    institution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get accounts by institution for the current user"""
    account_service = AccountService(db)
    accounts = account_service.get_accounts_by_institution(current_user.id, institution_id)
    
    return [AccountResponse.from_orm_account(account) for account in accounts]


@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an account (soft delete for data integrity)"""
    account_service = AccountService(db)
    success = account_service.delete_account(account_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return {"message": "Account deleted successfully"}