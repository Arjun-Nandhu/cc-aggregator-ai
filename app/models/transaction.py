from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Numeric, Text, Date, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    plaid_transaction_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    
    # Transaction details
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    iso_currency_code = Column(String, nullable=True)
    unofficial_currency_code = Column(String, nullable=True)
    
    # Categories and descriptions
    category = Column(JSON, nullable=True)  # Array of categories
    category_id = Column(String, nullable=True)
    merchant_name = Column(String, nullable=True)
    name = Column(String, nullable=False)
    original_description = Column(String, nullable=True)
    
    # Dates
    date = Column(Date, nullable=False)
    authorized_date = Column(Date, nullable=True)
    authorized_datetime = Column(DateTime(timezone=True), nullable=True)
    datetime = Column(DateTime(timezone=True), nullable=True)
    
    # Status and metadata
    pending = Column(Boolean, default=False)
    pending_transaction_id = Column(String, nullable=True)
    account_owner = Column(String, nullable=True)
    transaction_type = Column(String, nullable=True)
    transaction_code = Column(String, nullable=True)
    
    # Location data
    location = Column(JSON, nullable=True)
    
    # Payment metadata
    payment_meta = Column(JSON, nullable=True)
    
    # Personal finance category (Plaid's ML categorization)
    personal_finance_category = Column(JSON, nullable=True)
    
    # AI analysis fields
    ai_category = Column(String, nullable=True)
    ai_sentiment = Column(String, nullable=True)
    ai_tags = Column(JSON, nullable=True)
    ai_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")