from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.database import get_db, engine, Base
from app.models import User, Account, Transaction, Institution, AIAnalysis
from app.schemas import (
    UserCreate, User, Token, Account, Transaction, AIAnalysis,
    PlaidLinkToken, PlaidPublicToken, AnalysisRequest
)
from app.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.plaid_service import PlaidService
from app.services import FinancialDataService, AIAnalysisService
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@app.post("/plaid/link-token", response_model=PlaidLinkToken)
def create_plaid_link_token(current_user: User = Depends(get_current_user)):
    """Create a Plaid link token for connecting accounts"""
    try:
        result = PlaidService.create_link_token(str(current_user.id))
        return PlaidLinkToken(
            link_token=result['link_token'],
            expiration=datetime.fromisoformat(result['expiration'].replace('Z', '+00:00'))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create link token: {str(e)}"
        )


@app.post("/plaid/exchange-token")
def exchange_plaid_token(
    public_token_data: PlaidPublicToken,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exchange Plaid public token for access token and sync data"""
    try:
        # Exchange public token for access token
        access_token = PlaidService.exchange_public_token(public_token_data.public_token)
        
        # Sync user data
        financial_service = FinancialDataService(db)
        sync_result = financial_service.sync_user_data(current_user.id, access_token)
        
        return {
            "access_token": access_token,
            "sync_result": sync_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exchange token: {str(e)}"
        )


@app.get("/accounts", response_model=List[Account])
def get_user_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all accounts for the current user"""
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    return accounts


@app.get("/transactions", response_model=List[Transaction])
def get_user_transactions(
    limit: int = 100,
    offset: int = 0,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transactions for the current user"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.offset(offset).limit(limit).all()
    return transactions


@app.post("/analysis/spending-patterns")
def analyze_spending_patterns(
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze user's spending patterns"""
    analysis_service = AIAnalysisService(db)
    result = analysis_service.analyze_spending_patterns(current_user.id, days)
    return result


@app.post("/analysis/anomalies")
def detect_anomalies(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect unusual spending patterns"""
    analysis_service = AIAnalysisService(db)
    result = analysis_service.detect_anomalies(current_user.id, days)
    return result


@app.get("/analysis/history", response_model=List[AIAnalysis])
def get_analysis_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis history for the current user"""
    analyses = db.query(AIAnalysis).filter(
        AIAnalysis.user_id == current_user.id
    ).order_by(AIAnalysis.created_at.desc()).all()
    return analyses


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)