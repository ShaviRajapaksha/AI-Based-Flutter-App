from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.sql import func
from db import Base

class FinancialEntry(Base):
    __tablename__ = "financial_entries"

    id = Column(Integer, primary_key=True, index=True)
    # Core fields
    entry_type = Column(String(20), nullable=False) # SAVINGS | EXPENSES | INVESTMENTS | DEBT
    category = Column(String(50), nullable=True) # e.g., Groceries, Rent, Salary
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="LKR")

    # Meta / document fields
    vendor = Column(String(120), nullable=True)
    reference = Column(String(120), nullable=True) # receipt no / invoice no
    notes = Column(Text, nullable=True)

    # Dates
    entry_date = Column(Date, nullable=False) # date of transaction
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Provenance
    source = Column(String(20), default="manual") # manual | ocr
    raw_text = Column(Text, nullable=True) # OCR raw text