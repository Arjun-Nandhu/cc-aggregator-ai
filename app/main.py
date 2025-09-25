from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db, engine
from app.models import Base
from app.schemas import (
    UserCreate, UserResponse, LinkTokenResponse, ExchangeTokenRequest, 
    ExchangeTokenResponse, AccountResponse, TransactionResponse, 
    AIAnalysisResponse, AIAnalysisCreate
)
from app.crud import (
    get_user, get_user_by_email, create_user, get_accounts, get_transactions,
    create_account, create_transaction, create_ai_analysis, get_ai_analyses
)
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.plaid_client import plaid_client
from app.ai_analysis import FinancialAnalyzer
from app.models import User, Account, Transaction

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Financial Data Aggregator API",
    description="API for aggregating financial data from multiple institutions and AI analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = create_user(db=db, user=user, hashed_password=hashed_password)
    
    return db_user


@app.post("/auth/login")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    """Login user and return access token"""
    user = get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/plaid/link-token", response_model=LinkTokenResponse)
def create_link_token(current_user: User = Depends(get_current_user)):
    """Create a Plaid link token for connecting accounts"""
    link_token_data = plaid_client.create_link_token(str(current_user.id))
    return LinkTokenResponse(**link_token_data)


@app.post("/plaid/exchange-token", response_model=ExchangeTokenResponse)
def exchange_public_token(
    request: ExchangeTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exchange public token for access token and fetch account data"""
    try:
        # Exchange public token for access token
        exchange_data = plaid_client.exchange_public_token(request.public_token)
        access_token = exchange_data['access_token']
        item_id = exchange_data['item_id']
        
        # Fetch accounts from Plaid
        plaid_accounts = plaid_client.get_accounts(access_token)
        
        # Save accounts to database
        saved_accounts = []
        for account_data in plaid_accounts:
            # Check if institution exists, create if not
            institution = None
            if 'institution_id' in account_data:
                institution = db.query(Institution).filter(
                    Institution.plaid_institution_id == account_data['institution_id']
                ).first()
                
                if not institution:
                    # Fetch institution details from Plaid
                    inst_data = plaid_client.get_institution_by_id(account_data['institution_id'])
                    institution = Institution(
                        plaid_institution_id=inst_data['institution_id'],
                        name=inst_data['name'],
                        logo=inst_data.get('logo'),
                        primary_color=inst_data.get('primary_color'),
                        url=inst_data.get('url')
                    )
                    db.add(institution)
                    db.commit()
                    db.refresh(institution)
            
            # Create account record
            account = Account(
                user_id=current_user.id,
                plaid_account_id=account_data['account_id'],
                institution_id=institution.id if institution else None,
                name=account_data['name'],
                official_name=account_data.get('official_name'),
                type=account_data['type'],
                subtype=account_data.get('subtype'),
                mask=account_data.get('mask'),
                balance_available=account_data['balances'].get('available'),
                balance_current=account_data['balances'].get('current'),
                balance_limit=account_data['balances'].get('limit'),
                currency_code=account_data['balances'].get('iso_currency_code', 'USD')
            )
            db.add(account)
            saved_accounts.append(account)
        
        db.commit()
        
        # Fetch and save transactions
        transactions_data = plaid_client.get_transactions(access_token)
        saved_transactions = []
        
        for txn_data in transactions_data['transactions']:
            # Find corresponding account
            account = next(
                (acc for acc in saved_accounts if acc.plaid_account_id == txn_data['account_id']),
                None
            )
            
            if account:
                transaction = Transaction(
                    user_id=current_user.id,
                    account_id=account.id,
                    plaid_transaction_id=txn_data['transaction_id'],
                    amount=txn_data['amount'],
                    date=txn_data['date'],
                    name=txn_data['name'],
                    merchant_name=txn_data.get('merchant_name'),
                    category=txn_data.get('category'),
                    subcategory=txn_data.get('subcategory'),
                    account_owner=txn_data.get('account_owner'),
                    pending=txn_data.get('pending', False),
                    iso_currency_code=txn_data.get('iso_currency_code', 'USD'),
                    unofficial_currency_code=txn_data.get('unofficial_currency_code'),
                    location=txn_data.get('location'),
                    payment_meta=txn_data.get('payment_meta')
                )
                db.add(transaction)
                saved_transactions.append(transaction)
        
        db.commit()
        
        return ExchangeTokenResponse(
            access_token=access_token,
            item_id=item_id,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange token: {str(e)}"
        )


@app.get("/accounts", response_model=List[AccountResponse])
def get_user_accounts(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's connected accounts"""
    accounts = get_accounts(db, user_id=current_user.id, skip=skip, limit=limit)
    return accounts


@app.get("/transactions", response_model=List[TransactionResponse])
def get_user_transactions(
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transactions"""
    transactions = get_transactions(
        db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        account_id=account_id
    )
    return transactions


@app.post("/ai-analysis/spending-patterns")
def analyze_spending_patterns(
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze user's spending patterns"""
    analyzer = FinancialAnalyzer(db)
    analysis_data = analyzer.analyze_spending_patterns(current_user.id, days)
    
    # Save analysis to database
    ai_analysis = AIAnalysisCreate(
        analysis_type="spending_patterns",
        data=analysis_data,
        insights="\n".join(analysis_data.get('insights', [])),
        confidence_score=0.85
    )
    
    saved_analysis = create_ai_analysis(db, ai_analysis, current_user.id)
    
    return {
        "analysis_id": saved_analysis.id,
        "analysis_data": analysis_data,
        "created_at": saved_analysis.created_at
    }


@app.post("/ai-analysis/budget-performance")
def analyze_budget_performance(
    budget_categories: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze budget performance against set limits"""
    analyzer = FinancialAnalyzer(db)
    analysis_data = analyzer.analyze_budget_performance(current_user.id, budget_categories)
    
    # Save analysis to database
    ai_analysis = AIAnalysisCreate(
        analysis_type="budget_performance",
        data=analysis_data,
        insights="\n".join(analysis_data.get('insights', [])),
        confidence_score=0.90
    )
    
    saved_analysis = create_ai_analysis(db, ai_analysis, current_user.id)
    
    return {
        "analysis_id": saved_analysis.id,
        "analysis_data": analysis_data,
        "created_at": saved_analysis.created_at
    }


@app.post("/ai-analysis/anomaly-detection")
def detect_anomalies(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect unusual spending patterns"""
    analyzer = FinancialAnalyzer(db)
    analysis_data = analyzer.detect_anomalies(current_user.id, days)
    
    # Save analysis to database
    ai_analysis = AIAnalysisCreate(
        analysis_type="anomaly_detection",
        data=analysis_data,
        insights="\n".join(analysis_data.get('insights', [])),
        confidence_score=0.75
    )
    
    saved_analysis = create_ai_analysis(db, ai_analysis, current_user.id)
    
    return {
        "analysis_id": saved_analysis.id,
        "analysis_data": analysis_data,
        "created_at": saved_analysis.created_at
    }


@app.get("/ai-analysis", response_model=List[AIAnalysisResponse])
def get_ai_analyses(
    analysis_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's AI analysis results"""
    analyses = get_ai_analyses(db, user_id=current_user.id, analysis_type=analysis_type)
    return analyses


@app.get("/")
def read_root():
    return {"message": "Financial Data Aggregator API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)