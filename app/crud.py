from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.models import User, Account, Transaction, Institution, AIAnalysis
from app.schemas import UserCreate, AccountCreate, TransactionCreate, AIAnalysisCreate


# User CRUD operations
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate, hashed_password: str):
    db_user = User(
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Account CRUD operations
def get_accounts(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Account).filter(Account.user_id == user_id).offset(skip).limit(limit).all()


def get_account(db: Session, account_id: int, user_id: int):
    return db.query(Account).filter(
        and_(Account.id == account_id, Account.user_id == user_id)
    ).first()


def create_account(db: Session, account: AccountCreate, user_id: int):
    db_account = Account(**account.dict(), user_id=user_id)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def update_account_balance(db: Session, account_id: int, balance_available: float = None, balance_current: float = None):
    account = db.query(Account).filter(Account.id == account_id).first()
    if account:
        if balance_available is not None:
            account.balance_available = balance_available
        if balance_current is not None:
            account.balance_current = balance_current
        db.commit()
        db.refresh(account)
    return account


# Transaction CRUD operations
def get_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100, account_id: Optional[int] = None):
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    return query.order_by(desc(Transaction.date)).offset(skip).limit(limit).all()


def get_transaction(db: Session, transaction_id: int, user_id: int):
    return db.query(Transaction).filter(
        and_(Transaction.id == transaction_id, Transaction.user_id == user_id)
    ).first()


def create_transaction(db: Session, transaction: TransactionCreate, user_id: int):
    db_transaction = Transaction(**transaction.dict(), user_id=user_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def get_transactions_by_date_range(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    return db.query(Transaction).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
    ).order_by(desc(Transaction.date)).all()


def get_transactions_by_category(db: Session, user_id: int, category: str):
    return db.query(Transaction).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.category.contains([category])
        )
    ).all()


# Institution CRUD operations
def get_institution(db: Session, institution_id: int):
    return db.query(Institution).filter(Institution.id == institution_id).first()


def get_institution_by_plaid_id(db: Session, plaid_institution_id: str):
    return db.query(Institution).filter(Institution.plaid_institution_id == plaid_institution_id).first()


def create_institution(db: Session, institution_data: dict):
    db_institution = Institution(**institution_data)
    db.add(db_institution)
    db.commit()
    db.refresh(db_institution)
    return db_institution


# AI Analysis CRUD operations
def create_ai_analysis(db: Session, analysis: AIAnalysisCreate, user_id: int):
    db_analysis = AIAnalysis(**analysis.dict(), user_id=user_id)
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_ai_analyses(db: Session, user_id: int, analysis_type: Optional[str] = None):
    query = db.query(AIAnalysis).filter(AIAnalysis.user_id == user_id)
    if analysis_type:
        query = query.filter(AIAnalysis.analysis_type == analysis_type)
    return query.order_by(desc(AIAnalysis.created_at)).all()


def get_latest_ai_analysis(db: Session, user_id: int, analysis_type: str):
    return db.query(AIAnalysis).filter(
        and_(
            AIAnalysis.user_id == user_id,
            AIAnalysis.analysis_type == analysis_type
        )
    ).order_by(desc(AIAnalysis.created_at)).first()