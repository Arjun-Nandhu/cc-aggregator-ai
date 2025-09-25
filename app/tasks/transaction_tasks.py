from celery import current_task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.plaid_service import PlaidService
from app.services.transaction_service import TransactionService
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def sync_transactions_task(self, plaid_item_id: str, user_id: int):
    """Background task to sync transactions for a specific Plaid item"""
    db = SessionLocal()
    
    try:
        plaid_service = PlaidService()
        transaction_service = TransactionService(db)
        
        # Get Plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.plaid_item_id == plaid_item_id,
            PlaidItem.user_id == user_id,
            PlaidItem.is_active == True
        ).first()
        
        if not plaid_item:
            logger.error(f"Plaid item {plaid_item_id} not found for user {user_id}")
            return {"error": "Plaid item not found"}
        
        # Update task state
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Syncing transactions...', 'progress': 25}
        )
        
        # Sync transactions using cursor
        sync_data = await plaid_service.sync_transactions(
            plaid_item.plaid_access_token,
            cursor=plaid_item.cursor
        )
        
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Processing transactions...', 'progress': 50}
        )
        
        # Process transactions
        added_count = 0
        modified_count = 0
        removed_count = 0
        
        if sync_data["added"]:
            transaction_service.sync_transactions_from_plaid(
                sync_data["added"], user_id
            )
            added_count = len(sync_data["added"])
        
        if sync_data["modified"]:
            transaction_service.sync_transactions_from_plaid(
                sync_data["modified"], user_id
            )
            modified_count = len(sync_data["modified"])
        
        if sync_data["removed"]:
            transaction_service.remove_transactions_by_plaid_ids(
                sync_data["removed"], user_id
            )
            removed_count = len(sync_data["removed"])
        
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Updating sync cursor...', 'progress': 75}
        )
        
        # Update cursor and last sync time
        plaid_item.cursor = sync_data["next_cursor"]
        plaid_item.last_sync = datetime.utcnow()
        db.commit()
        
        result = {
            "status": "completed",
            "added": added_count,
            "modified": modified_count,
            "removed": removed_count,
            "has_more": sync_data["has_more"],
            "last_sync": plaid_item.last_sync.isoformat()
        }
        
        logger.info(f"Sync completed for item {plaid_item_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing transactions for item {plaid_item_id}: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def sync_all_transactions_task(self):
    """Background task to sync transactions for all active Plaid items"""
    db = SessionLocal()
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Getting active Plaid items...', 'progress': 10}
        )
        
        # Get all active Plaid items
        plaid_items = db.query(PlaidItem).filter(
            PlaidItem.is_active == True
        ).all()
        
        total_items = len(plaid_items)
        synced_items = 0
        failed_items = 0
        
        for i, plaid_item in enumerate(plaid_items):
            try:
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Syncing item {i+1}/{total_items}...',
                        'progress': 10 + (i * 80 // total_items)
                    }
                )
                
                # Trigger sync task for each item
                sync_transactions_task.delay(plaid_item.plaid_item_id, plaid_item.user_id)
                synced_items += 1
                
            except Exception as e:
                logger.error(f"Failed to sync item {plaid_item.plaid_item_id}: {str(e)}")
                failed_items += 1
        
        result = {
            "status": "completed",
            "total_items": total_items,
            "synced_items": synced_items,
            "failed_items": failed_items
        }
        
        logger.info(f"Bulk sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk sync: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2})
def analyze_transactions_task(self, user_id: int, transaction_ids: List[int] = None):
    """Background task to analyze transactions using AI"""
    db = SessionLocal()
    
    try:
        transaction_service = TransactionService(db)
        
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Getting transactions for analysis...', 'progress': 20}
        )
        
        # Get transactions to analyze
        if transaction_ids:
            transactions = db.query(Transaction).filter(
                Transaction.id.in_(transaction_ids),
                Transaction.user_id == user_id
            ).all()
        else:
            # Analyze recent transactions without AI analysis
            cutoff_date = datetime.now() - timedelta(days=7)
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.created_at >= cutoff_date,
                Transaction.ai_category.is_(None)
            ).limit(100).all()
        
        total_transactions = len(transactions)
        analyzed_count = 0
        
        current_task.update_state(
            state='PROGRESS',
            meta={'status': f'Analyzing {total_transactions} transactions...', 'progress': 40}
        )
        
        for i, transaction in enumerate(transactions):
            try:
                # Analyze transaction using AI (placeholder for actual AI integration)
                ai_analysis = await analyze_transaction_with_ai(transaction)
                
                # Update transaction with AI analysis
                transaction_service.update_transaction(
                    transaction.id,
                    user_id,
                    {
                        "ai_category": ai_analysis.get("category"),
                        "ai_sentiment": ai_analysis.get("sentiment"),
                        "ai_tags": ai_analysis.get("tags", []),
                        "ai_notes": ai_analysis.get("notes")
                    }
                )
                
                analyzed_count += 1
                
                # Update progress
                progress = 40 + (i * 50 // total_transactions)
                current_task.update_state(
                    state='PROGRESS',
                    meta={'status': f'Analyzed {i+1}/{total_transactions} transactions...', 'progress': progress}
                )
                
            except Exception as e:
                logger.error(f"Failed to analyze transaction {transaction.id}: {str(e)}")
        
        result = {
            "status": "completed",
            "total_transactions": total_transactions,
            "analyzed_count": analyzed_count
        }
        
        logger.info(f"Transaction analysis completed for user {user_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing transactions for user {user_id}: {str(e)}")
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def analyze_recent_transactions_task(self):
    """Background task to analyze recent transactions for all users"""
    db = SessionLocal()
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Getting users with recent transactions...', 'progress': 10}
        )
        
        # Get users with recent transactions that need analysis
        cutoff_date = datetime.now() - timedelta(hours=2)
        
        users_with_new_transactions = db.query(Transaction.user_id).filter(
            Transaction.created_at >= cutoff_date,
            Transaction.ai_category.is_(None)
        ).distinct().all()
        
        total_users = len(users_with_new_transactions)
        processed_users = 0
        
        for i, (user_id,) in enumerate(users_with_new_transactions):
            try:
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Processing user {i+1}/{total_users}...',
                        'progress': 10 + (i * 80 // total_users)
                    }
                )
                
                # Trigger analysis task for user
                analyze_transactions_task.delay(user_id)
                processed_users += 1
                
            except Exception as e:
                logger.error(f"Failed to trigger analysis for user {user_id}: {str(e)}")
        
        result = {
            "status": "completed",
            "total_users": total_users,
            "processed_users": processed_users
        }
        
        logger.info(f"Recent transaction analysis completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in recent transaction analysis: {str(e)}")
        raise
    finally:
        db.close()


async def analyze_transaction_with_ai(transaction: Transaction) -> Dict[str, Any]:
    """Analyze a transaction using AI (placeholder implementation)"""
    # This is a placeholder for actual AI integration
    # You would implement this with OpenAI, or other AI services
    
    # Basic rule-based categorization as example
    category_mapping = {
        "Food and Drink": ["restaurant", "grocery", "coffee", "bar"],
        "Transportation": ["uber", "lyft", "gas", "parking", "metro"],
        "Shopping": ["amazon", "target", "walmart", "mall"],
        "Healthcare": ["pharmacy", "doctor", "hospital", "dental"],
        "Entertainment": ["movie", "netflix", "spotify", "gaming"],
        "Utilities": ["electric", "water", "internet", "phone"],
    }
    
    transaction_name = transaction.name.lower()
    merchant_name = (transaction.merchant_name or "").lower()
    text_to_analyze = f"{transaction_name} {merchant_name}"
    
    detected_category = "Other"
    for category, keywords in category_mapping.items():
        if any(keyword in text_to_analyze for keyword in keywords):
            detected_category = category
            break
    
    # Determine sentiment based on amount and category
    sentiment = "neutral"
    if transaction.amount > 100:
        sentiment = "negative"  # Large expense
    elif detected_category in ["Entertainment", "Food and Drink"]:
        sentiment = "positive"  # Enjoyable spending
    
    # Generate tags
    tags = []
    if transaction.pending:
        tags.append("pending")
    if transaction.amount > 500:
        tags.append("large-expense")
    if detected_category != "Other":
        tags.append(detected_category.lower().replace(" ", "-"))
    
    return {
        "category": detected_category,
        "sentiment": sentiment,
        "tags": tags,
        "notes": f"Auto-categorized based on transaction details. Amount: ${transaction.amount}"
    }