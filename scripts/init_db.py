#!/usr/bin/env python3
"""
Initialize the database with sample data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, Institution, Account, Transaction, AIAnalysis
from app.auth import get_password_hash
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample data for testing"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create sample user
        user = User(
            email="demo@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create sample institution
        institution = Institution(
            name="Demo Bank",
            plaid_institution_id="ins_123456",
            logo_url="https://example.com/logo.png",
            primary_color="#1a73e8"
        )
        db.add(institution)
        db.commit()
        db.refresh(institution)
        
        # Create sample accounts
        accounts_data = [
            {
                "name": "Checking Account",
                "type": "depository",
                "subtype": "checking",
                "mask": "0000"
            },
            {
                "name": "Savings Account", 
                "type": "depository",
                "subtype": "savings",
                "mask": "1111"
            },
            {
                "name": "Credit Card",
                "type": "credit",
                "subtype": "credit_card",
                "mask": "2222"
            }
        ]
        
        accounts = []
        for account_data in accounts_data:
            account = Account(
                user_id=user.id,
                institution_id=institution.id,
                plaid_account_id=f"account_{random.randint(1000, 9999)}",
                name=account_data["name"],
                type=account_data["type"],
                subtype=account_data["subtype"],
                mask=account_data["mask"]
            )
            db.add(account)
            accounts.append(account)
        
        db.commit()
        
        # Create sample transactions
        categories = [
            ["Food and Drink", "Restaurants"],
            ["Shops", "Supermarkets and Groceries"],
            ["Transportation", "Gas Stations"],
            ["Recreation", "Entertainment"],
            ["Service", "Financial"],
            ["Healthcare", "Pharmacies"]
        ]
        
        merchants = [
            "Starbucks", "McDonald's", "Walmart", "Target", "Shell", "Exxon",
            "Netflix", "Spotify", "Amazon", "Uber", "Lyft", "Apple Store"
        ]
        
        transactions = []
        for i in range(100):  # Create 100 sample transactions
            category = random.choice(categories)
            merchant = random.choice(merchants)
            amount = round(random.uniform(-500, -5), 2)  # Negative amounts for spending
            date = datetime.now() - timedelta(days=random.randint(0, 90))
            
            transaction = Transaction(
                user_id=user.id,
                account_id=random.choice(accounts).id,
                plaid_transaction_id=f"txn_{random.randint(10000, 99999)}",
                amount=amount,
                date=date,
                name=merchant,
                merchant_name=merchant,
                category=category,
                subcategory=category[1:],
                is_pending=random.choice([True, False]),
                raw_data={
                    "merchant_name": merchant,
                    "category": category,
                    "amount": amount
                }
            )
            db.add(transaction)
            transactions.append(transaction)
        
        db.commit()
        
        # Create sample AI analysis
        analysis = AIAnalysis(
            user_id=user.id,
            analysis_type="spending_patterns",
            results={
                "total_spending": -2500.50,
                "avg_daily_spending": -27.78,
                "category_breakdown": {
                    "Food and Drink": -800.25,
                    "Transportation": -450.00,
                    "Shops": -1200.25
                },
                "top_merchants": {
                    "Starbucks": -150.00,
                    "Walmart": -300.50,
                    "Shell": -200.25
                }
            },
            confidence_score=0.85
        )
        db.add(analysis)
        db.commit()
        
        print("✅ Sample data created successfully!")
        print(f"📧 Demo user: demo@example.com")
        print(f"🔑 Password: password123")
        print(f"🏦 Created {len(accounts)} accounts")
        print(f"💳 Created {len(transactions)} transactions")
        print(f"🤖 Created AI analysis")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()