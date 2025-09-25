from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.utils.auth import get_current_active_user
from app.services.plaid_service import PlaidService
from app.services.account_service import AccountService
from app.services.transaction_service import TransactionService
from app.models.user import User
from app.models.institution import Institution
from app.models.plaid_item import PlaidItem
from app.schemas.plaid import PlaidLinkTokenRequest, PlaidExchangeRequest, PlaidLinkResponse
from datetime import datetime, timedelta

router = APIRouter()


@router.post("/link-token", response_model=PlaidLinkResponse)
async def create_link_token(
    request: PlaidLinkTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create Plaid Link token for user authentication"""
    plaid_service = PlaidService()
    
    try:
        link_token_data = await plaid_service.create_link_token(
            user_id=current_user.id,
            webhook_url=request.webhook_url
        )
        return PlaidLinkResponse(**link_token_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create link token: {str(e)}"
        )


@router.post("/exchange-token")
async def exchange_public_token(
    request: PlaidExchangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Exchange public token for access token and fetch initial data"""
    plaid_service = PlaidService()
    account_service = AccountService(db)
    transaction_service = TransactionService(db)
    
    try:
        # Exchange public token for access token
        token_data = await plaid_service.exchange_public_token(request.public_token)
        access_token = token_data["access_token"]
        item_id = token_data["item_id"]
        
        # Get accounts and item info
        accounts_data, item_data = await plaid_service.get_accounts(access_token)
        institution_id = item_data["institution_id"]
        
        # Get or create institution
        institution = db.query(Institution).filter(
            Institution.plaid_institution_id == institution_id
        ).first()
        
        if not institution:
            institution_data = await plaid_service.get_institution(institution_id)
            institution = Institution(
                plaid_institution_id=institution_data["institution_id"],
                name=institution_data["name"],
                country=institution_data.get("country", "US"),
                url=institution_data.get("url"),
                primary_color=institution_data.get("primary_color"),
                logo=institution_data.get("logo")
            )
            db.add(institution)
            db.commit()
            db.refresh(institution)
        
        # Create Plaid item
        plaid_item = PlaidItem(
            plaid_item_id=item_id,
            plaid_access_token=access_token,
            user_id=current_user.id,
            institution_id=institution.id,
            webhook_url=request.webhook_url
        )
        db.add(plaid_item)
        db.commit()
        db.refresh(plaid_item)
        
        # Sync accounts
        account_service.sync_accounts_from_plaid(
            accounts_data, current_user.id, plaid_item.id, institution.id
        )
        
        # Fetch initial transactions (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        transactions_data, total_transactions = await plaid_service.get_transactions(
            access_token, start_date, end_date
        )
        
        # Sync transactions
        transaction_service.sync_transactions_from_plaid(transactions_data, current_user.id)
        
        return {
            "message": "Successfully connected to financial institution",
            "institution": institution.name,
            "accounts_synced": len(accounts_data),
            "transactions_synced": len(transactions_data),
            "item_id": item_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange token: {str(e)}"
        )


@router.post("/sync-transactions/{item_id}")
async def sync_transactions(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually sync transactions for a Plaid item"""
    plaid_service = PlaidService()
    transaction_service = TransactionService(db)
    
    # Get Plaid item
    plaid_item = db.query(PlaidItem).filter(
        PlaidItem.plaid_item_id == item_id,
        PlaidItem.user_id == current_user.id,
        PlaidItem.is_active == True
    ).first()
    
    if not plaid_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plaid item not found"
        )
    
    try:
        # Use cursor-based sync for better performance
        sync_data = await plaid_service.sync_transactions(
            plaid_item.plaid_access_token,
            cursor=plaid_item.cursor
        )
        
        # Process added transactions
        if sync_data["added"]:
            transaction_service.sync_transactions_from_plaid(
                sync_data["added"], current_user.id
            )
        
        # Process modified transactions
        if sync_data["modified"]:
            transaction_service.sync_transactions_from_plaid(
                sync_data["modified"], current_user.id
            )
        
        # Process removed transactions
        if sync_data["removed"]:
            transaction_service.remove_transactions_by_plaid_ids(
                sync_data["removed"], current_user.id
            )
        
        # Update cursor
        plaid_item.cursor = sync_data["next_cursor"]
        plaid_item.last_sync = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Transactions synced successfully",
            "added": len(sync_data["added"]),
            "modified": len(sync_data["modified"]),
            "removed": len(sync_data["removed"]),
            "has_more": sync_data["has_more"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync transactions: {str(e)}"
        )


@router.get("/items")
async def get_plaid_items(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all Plaid items for the current user"""
    plaid_items = db.query(PlaidItem).filter(
        PlaidItem.user_id == current_user.id,
        PlaidItem.is_active == True
    ).all()
    
    items_data = []
    for item in plaid_items:
        items_data.append({
            "item_id": item.plaid_item_id,
            "institution": {
                "id": item.institution.id,
                "name": item.institution.name,
                "logo": item.institution.logo
            },
            "last_sync": item.last_sync.isoformat() if item.last_sync else None,
            "created_at": item.created_at.isoformat()
        })
    
    return {"items": items_data}


@router.delete("/items/{item_id}")
async def remove_plaid_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a Plaid item and all associated data"""
    plaid_item = db.query(PlaidItem).filter(
        PlaidItem.plaid_item_id == item_id,
        PlaidItem.user_id == current_user.id
    ).first()
    
    if not plaid_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plaid item not found"
        )
    
    # Deactivate the item instead of deleting to preserve data integrity
    plaid_item.is_active = False
    db.commit()
    
    return {"message": "Plaid item removed successfully"}