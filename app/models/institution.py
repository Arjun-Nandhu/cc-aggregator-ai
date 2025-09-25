from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    plaid_institution_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    url = Column(String, nullable=True)
    primary_color = Column(String, nullable=True)
    logo = Column(Text, nullable=True)  # base64 encoded logo
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plaid_items = relationship("PlaidItem", back_populates="institution")
    accounts = relationship("Account", back_populates="institution")