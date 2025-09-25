from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")


class Institution(Base):
    __tablename__ = "institutions"
    
    id = Column(Integer, primary_key=True, index=True)
    plaid_institution_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    logo = Column(String)
    primary_color = Column(String)
    url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plaid_account_id = Column(String, unique=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    name = Column(String, nullable=False)
    official_name = Column(String)
    type = Column(String, nullable=False)  # depository, credit, loan, investment, etc.
    subtype = Column(String)  # checking, savings, credit_card, etc.
    mask = Column(String)  # Last 4 digits
    balance_available = Column(Float)
    balance_current = Column(Float)
    balance_limit = Column(Float)
    currency_code = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    institution = relationship("Institution")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    plaid_transaction_id = Column(String, unique=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    name = Column(String, nullable=False)
    merchant_name = Column(String)
    category = Column(JSON)  # Array of category strings
    subcategory = Column(JSON)  # Array of subcategory strings
    account_owner = Column(String)
    pending = Column(Boolean, default=False)
    iso_currency_code = Column(String, default="USD")
    unofficial_currency_code = Column(String)
    location = Column(JSON)  # Location data
    payment_meta = Column(JSON)  # Payment metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    analysis_type = Column(String, nullable=False)  # spending_patterns, budget_analysis, etc.
    data = Column(JSON, nullable=False)  # Analysis results
    insights = Column(Text)
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")