from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta

from app.core.database import get_db
from app.utils.auth import get_current_active_user
from app.services.transaction_service import TransactionService
from app.tasks.transaction_tasks import analyze_transactions_task
from app.models.user import User

router = APIRouter()


@router.post("/analyze-transactions")
async def trigger_transaction_analysis(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    transaction_ids: Optional[List[int]] = None
):
    """Trigger AI analysis for user transactions"""
    # Trigger background analysis task
    task = analyze_transactions_task.delay(current_user.id, transaction_ids)
    
    return {
        "message": "Transaction analysis started",
        "task_id": task.id,
        "status": "processing"
    }


@router.get("/spending-insights")
async def get_spending_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    period: str = "30d"
):
    """Get AI-powered spending insights and recommendations"""
    transaction_service = TransactionService(db)
    
    # Set default date range
    if not end_date:
        end_date = date.today()
    
    if not start_date:
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
    
    # Get transaction analytics
    analytics = transaction_service.get_transaction_analytics(
        current_user.id, start_date, end_date
    )
    
    # Get transactions with AI analysis
    transactions = transaction_service.get_transactions_by_user(
        current_user.id, limit=1000
    )
    
    # Analyze AI categorization
    ai_categories = {}
    ai_sentiments = {}
    ai_tagged_count = 0
    
    for transaction in transactions:
        if transaction.ai_category:
            ai_categories[transaction.ai_category] = ai_categories.get(transaction.ai_category, 0) + 1
        
        if transaction.ai_sentiment:
            ai_sentiments[transaction.ai_sentiment] = ai_sentiments.get(transaction.ai_sentiment, 0) + 1
        
        if transaction.ai_tags:
            ai_tagged_count += 1
    
    # Generate insights
    insights = generate_spending_insights(analytics, ai_categories, ai_sentiments)
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": (end_date - start_date).days
        },
        "ai_analysis": {
            "total_transactions": len(transactions),
            "ai_tagged_transactions": ai_tagged_count,
            "ai_categories": ai_categories,
            "ai_sentiments": ai_sentiments
        },
        "insights": insights,
        **analytics
    }


@router.get("/category-trends")
async def get_category_trends(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    months: int = 6
):
    """Get spending trends by AI category over time"""
    transaction_service = TransactionService(db)
    
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    transactions = transaction_service.get_transactions_by_user(
        current_user.id, limit=10000
    )
    
    # Filter by date range and group by month and AI category
    monthly_trends = {}
    
    for transaction in transactions:
        if transaction.date < start_date or transaction.date > end_date:
            continue
        
        month_key = transaction.date.strftime("%Y-%m")
        ai_category = transaction.ai_category or "Uncategorized"
        
        if month_key not in monthly_trends:
            monthly_trends[month_key] = {}
        
        if ai_category not in monthly_trends[month_key]:
            monthly_trends[month_key][ai_category] = 0
        
        monthly_trends[month_key][ai_category] += float(transaction.amount)
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "months": months
        },
        "category_trends": monthly_trends
    }


@router.get("/recommendations")
async def get_ai_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered spending recommendations"""
    transaction_service = TransactionService(db)
    
    # Get recent transactions for analysis
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    
    analytics = transaction_service.get_transaction_analytics(
        current_user.id, start_date, end_date
    )
    
    # Generate personalized recommendations
    recommendations = generate_ai_recommendations(analytics, current_user.id)
    
    return {
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat()
    }


def generate_spending_insights(
    analytics: Dict[str, Any], 
    ai_categories: Dict[str, int], 
    ai_sentiments: Dict[str, int]
) -> List[Dict[str, Any]]:
    """Generate spending insights based on analytics and AI data"""
    insights = []
    
    # Income vs Expenses insight
    summary = analytics.get("summary", {})
    total_income = summary.get("total_income", 0)
    total_expenses = summary.get("total_expenses", 0)
    
    if total_income > 0:
        savings_rate = ((total_income - total_expenses) / total_income) * 100
        if savings_rate > 20:
            insights.append({
                "type": "positive",
                "category": "savings",
                "title": "Excellent Savings Rate",
                "description": f"You're saving {savings_rate:.1f}% of your income. Keep up the great work!",
                "value": savings_rate
            })
        elif savings_rate < 10:
            insights.append({
                "type": "warning",
                "category": "savings",
                "title": "Low Savings Rate",
                "description": f"You're only saving {savings_rate:.1f}% of your income. Consider reducing expenses.",
                "value": savings_rate
            })
    
    # Top spending category insight
    top_categories = analytics.get("top_categories", [])
    if top_categories:
        top_category = top_categories[0]
        insights.append({
            "type": "info",
            "category": "spending",
            "title": "Top Spending Category",
            "description": f"You spent the most on {top_category['category']} (${top_category['amount']:.2f})",
            "value": top_category['amount']
        })
    
    # AI sentiment analysis
    if ai_sentiments:
        negative_count = ai_sentiments.get("negative", 0)
        total_analyzed = sum(ai_sentiments.values())
        
        if negative_count / total_analyzed > 0.6:
            insights.append({
                "type": "warning",
                "category": "sentiment",
                "title": "High Stress Spending",
                "description": f"{(negative_count/total_analyzed)*100:.1f}% of your transactions show negative sentiment patterns",
                "value": negative_count
            })
    
    return insights


def generate_ai_recommendations(analytics: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
    """Generate AI-powered recommendations"""
    recommendations = []
    
    summary = analytics.get("summary", {})
    top_categories = analytics.get("top_categories", [])
    monthly_trends = analytics.get("monthly_trends", {})
    
    # High spending category recommendation
    if top_categories and len(top_categories) > 0:
        top_category = top_categories[0]
        if top_category['amount'] > 1000:
            recommendations.append({
                "type": "cost_reduction",
                "priority": "high",
                "title": f"Reduce {top_category['category']} Spending",
                "description": f"Consider ways to reduce spending in {top_category['category']}. Even a 10% reduction could save you ${top_category['amount'] * 0.1:.2f}",
                "potential_savings": top_category['amount'] * 0.1,
                "category": top_category['category']
            })
    
    # Budget recommendation
    total_expenses = summary.get("total_expenses", 0)
    if total_expenses > 0:
        recommendations.append({
            "type": "budgeting",
            "priority": "medium",
            "title": "Set Category Budgets",
            "description": "Based on your spending patterns, consider setting monthly budgets for your top categories",
            "suggested_budgets": {
                cat['category']: cat['amount'] * 1.1 
                for cat in top_categories[:5]
            }
        })
    
    # Savings goal recommendation
    total_income = summary.get("total_income", 0)
    if total_income > 0:
        current_savings = total_income - total_expenses
        recommended_savings = total_income * 0.2  # 20% savings rate
        
        if current_savings < recommended_savings:
            recommendations.append({
                "type": "savings",
                "priority": "high",
                "title": "Increase Emergency Fund",
                "description": f"Try to save ${recommended_savings - current_savings:.2f} more per month to reach a 20% savings rate",
                "target_amount": recommended_savings - current_savings
            })
    
    return recommendations