import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from app.models import Transaction, Account
from app.crud import get_transactions_by_date_range, get_transactions_by_category


class FinancialAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def analyze_spending_patterns(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Analyze spending patterns over the specified period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = get_transactions_by_date_range(self.db, user_id, start_date, end_date)
        
        if not transactions:
            return {"error": "No transactions found for analysis"}
        
        # Convert to DataFrame for analysis
        data = []
        for txn in transactions:
            data.append({
                'amount': txn.amount,
                'date': txn.date,
                'category': txn.category[0] if txn.category else 'Other',
                'merchant': txn.merchant_name or txn.name,
                'account_type': txn.account.type
            })
        
        df = pd.DataFrame(data)
        
        # Spending analysis
        total_spending = df[df['amount'] < 0]['amount'].sum()
        avg_daily_spending = abs(total_spending) / days
        
        # Category analysis
        category_spending = df[df['amount'] < 0].groupby('category')['amount'].sum().sort_values()
        
        # Monthly spending trends
        df['month'] = df['date'].dt.to_period('M')
        monthly_spending = df[df['amount'] < 0].groupby('month')['amount'].sum()
        
        # Top merchants
        top_merchants = df[df['amount'] < 0].groupby('merchant')['amount'].sum().sort_values().head(10)
        
        return {
            "analysis_type": "spending_patterns",
            "period_days": days,
            "total_spending": abs(total_spending),
            "average_daily_spending": avg_daily_spending,
            "category_breakdown": category_spending.to_dict(),
            "monthly_trends": monthly_spending.to_dict(),
            "top_merchants": top_merchants.to_dict(),
            "transaction_count": len(transactions),
            "insights": self._generate_spending_insights(category_spending, avg_daily_spending)
        }

    def analyze_budget_performance(self, user_id: int, budget_categories: Dict[str, float]) -> Dict[str, Any]:
        """Analyze budget performance against set limits"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Monthly budget analysis
        
        transactions = get_transactions_by_date_range(self.db, user_id, start_date, end_date)
        
        if not transactions:
            return {"error": "No transactions found for budget analysis"}
        
        # Calculate spending by category
        category_spending = {}
        for txn in transactions:
            if txn.amount < 0 and txn.category:
                category = txn.category[0]
                category_spending[category] = category_spending.get(category, 0) + abs(txn.amount)
        
        # Compare against budget
        budget_performance = {}
        for category, budget_limit in budget_categories.items():
            spent = category_spending.get(category, 0)
            remaining = budget_limit - spent
            percentage_used = (spent / budget_limit * 100) if budget_limit > 0 else 0
            
            budget_performance[category] = {
                "budget_limit": budget_limit,
                "spent": spent,
                "remaining": remaining,
                "percentage_used": percentage_used,
                "over_budget": spent > budget_limit
            }
        
        return {
            "analysis_type": "budget_performance",
            "budget_performance": budget_performance,
            "total_budget": sum(budget_categories.values()),
            "total_spent": sum(category_spending.values()),
            "insights": self._generate_budget_insights(budget_performance)
        }

    def detect_anomalies(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Detect unusual spending patterns"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        transactions = get_transactions_by_date_range(self.db, user_id, start_date, end_date)
        
        if not transactions:
            return {"error": "No transactions found for anomaly detection"}
        
        # Convert to DataFrame
        data = []
        for txn in transactions:
            data.append({
                'amount': abs(txn.amount) if txn.amount < 0 else 0,
                'date': txn.date,
                'category': txn.category[0] if txn.category else 'Other'
            })
        
        df = pd.DataFrame(data)
        
        # Detect high-value transactions (above 95th percentile)
        high_value_threshold = df['amount'].quantile(0.95)
        high_value_transactions = df[df['amount'] > high_value_threshold]
        
        # Detect unusual spending by category
        category_anomalies = {}
        for category in df['category'].unique():
            category_data = df[df['category'] == category]['amount']
            if len(category_data) > 5:  # Need enough data points
                mean_spending = category_data.mean()
                std_spending = category_data.std()
                threshold = mean_spending + (2 * std_spending)  # 2 standard deviations
                anomalies = category_data[category_data > threshold]
                if not anomalies.empty:
                    category_anomalies[category] = {
                        "anomalous_transactions": len(anomalies),
                        "total_anomalous_amount": anomalies.sum(),
                        "threshold": threshold
                    }
        
        return {
            "analysis_type": "anomaly_detection",
            "high_value_threshold": high_value_threshold,
            "high_value_transactions": high_value_transactions.to_dict('records'),
            "category_anomalies": category_anomalies,
            "insights": self._generate_anomaly_insights(high_value_transactions, category_anomalies)
        }

    def _generate_spending_insights(self, category_spending, avg_daily_spending) -> List[str]:
        """Generate insights from spending analysis"""
        insights = []
        
        if avg_daily_spending > 100:
            insights.append("Your daily spending is above average. Consider reviewing your expenses.")
        
        top_category = category_spending.index[-1] if not category_spending.empty else None
        if top_category:
            insights.append(f"Your highest spending category is {top_category}.")
        
        if len(category_spending) > 10:
            insights.append("You have diverse spending across many categories.")
        
        return insights

    def _generate_budget_insights(self, budget_performance) -> List[str]:
        """Generate insights from budget analysis"""
        insights = []
        
        over_budget_categories = [cat for cat, perf in budget_performance.items() if perf['over_budget']]
        if over_budget_categories:
            insights.append(f"You're over budget in: {', '.join(over_budget_categories)}")
        
        under_budget_categories = [cat for cat, perf in budget_performance.items() if perf['percentage_used'] < 50]
        if under_budget_categories:
            insights.append(f"You're well under budget in: {', '.join(under_budget_categories)}")
        
        return insights

    def _generate_anomaly_insights(self, high_value_transactions, category_anomalies) -> List[str]:
        """Generate insights from anomaly detection"""
        insights = []
        
        if not high_value_transactions.empty:
            insights.append(f"Found {len(high_value_transactions)} high-value transactions.")
        
        if category_anomalies:
            insights.append(f"Unusual spending detected in {len(category_anomalies)} categories.")
        
        return insights