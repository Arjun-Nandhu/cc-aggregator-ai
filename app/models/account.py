from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Numeric, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    plaid_account_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    plaid_item_id = Column(Integer, ForeignKey("plaid_items.id"), nullable=False)
    
    # Account details
    name = Column(String, nullable=False)
    official_name = Column(String, nullable=True)
    type = Column(String, nullable=False)  # depository, credit, loan, investment
    subtype = Column(String, nullable=False)  # checking, savings, credit card, etc.
    mask = Column(String, nullable=True)  # Last 4 digits
    
    # Balance information
    available_balance = Column(Numeric(precision=10, scale=2), nullable=True)
    current_balance = Column(Numeric(precision=10, scale=2), nullable=True)
    limit_balance = Column(Numeric(precision=10, scale=2), nullable=True)
    iso_currency_code = Column(String, nullable=True)
    unofficial_currency_code = Column(String, nullable=True)
    
    # Metadata
    verification_status = Column(String, nullable=True)
    persistent_account_id = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="accounts")
    institution = relationship("Institution", back_populates="accounts")
    plaid_item = relationship("PlaidItem", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")