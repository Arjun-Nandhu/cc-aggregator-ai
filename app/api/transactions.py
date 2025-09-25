from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.utils.auth import get_current_active_user
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionResponse, TransactionFilter
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for filtering transactions"),
    end_date: Optional[date] = Query(None, description="End date for filtering transactions"),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    category: Optional[str] = Query(None, description="Category filter"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
    max_amount: Optional[float] = Query(None, description="Maximum amount filter"),
    merchant_name: Optional[str] = Query(None, description="Merchant name filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip")
):
    """Get transactions for the current user with optional filtering"""
    transaction_service = TransactionService(db)
    
    # Parse account_ids if provided
    parsed_account_ids = None
    if account_ids:
        try:
            parsed_account_ids = [int(id.strip()) for id in account_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid account_ids format. Use comma-separated integers."
            )
    
    # Create filter object
    filters = TransactionFilter(
        start_date=start_date,
        end_date=end_date,
        account_ids=parsed_account_ids,
        category=category,
        min_amount=min_amount,
        max_amount=max_amount,
        merchant_name=merchant_name
    )
    
    transactions = transaction_service.get_transactions_by_user(
        current_user.id, filters, limit, offset
    )
    
    return transactions


@router.get("/account/{account_id}", response_model=List[TransactionResponse])
async def get_transactions_by_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get transactions for a specific account"""
    transaction_service = TransactionService(db)
    transactions = transaction_service.get_transactions_by_account(account_id, current_user.id)
    
    return transactions


@router.get("/analytics")
async def get_transaction_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for analytics"),
    end_date: Optional[date] = Query(None, description="End date for analytics"),
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y")
):
    """Get transaction analytics and insights"""
    transaction_service = TransactionService(db)
    
    # Set default date range based on period
    if not end_date:
        end_date = date.today()
    
    if not start_date:
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
    
    analytics = transaction_service.get_transaction_analytics(
        current_user.id, start_date, end_date
    )
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": (end_date - start_date).days
        },
        **analytics
    }


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update transaction with AI analysis data or custom fields"""
    transaction_service = TransactionService(db)
    
    # Only allow certain fields to be updated
    allowed_fields = {
        "ai_category", "ai_sentiment", "ai_tags", "ai_notes"
    }
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided for update"
        )
    
    updated_transaction = transaction_service.update_transaction(
        transaction_id, current_user.id, filtered_updates
    )
    
    return updated_transaction


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    transaction_service = TransactionService(db)
    success = transaction_service.delete_transaction(transaction_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return {"message": "Transaction deleted successfully"}


@router.get("/search")
async def search_transactions(
    q: str = Query(..., description="Search query for transaction names and descriptions"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500, description="Number of results to return")
):
    """Search transactions by name, description, or merchant"""
    transaction_service = TransactionService(db)
    
    # Use merchant_name filter for search (could be extended to search multiple fields)
    filters = TransactionFilter(merchant_name=q)
    
    transactions = transaction_service.get_transactions_by_user(
        current_user.id, filters, limit, 0
    )
    
    return {
        "query": q,
        "results": transactions,
        "count": len(transactions)
    }