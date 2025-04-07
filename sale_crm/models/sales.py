from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    contact_id = Column(Integer, ForeignKey("contact_list.id"))
    status_id = Column(Integer, ForeignKey("sale_status.id"))
    outcome_id = Column(Integer, ForeignKey("sales_outcomes.id"))

    expected_closure_date = Column(DateTime(timezone=True), nullable=True)
    payment_status = Column(String, nullable=True)
    deal_value = Column(Numeric, nullable=True)
    sale_amount = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # 🔗 Relationships
    user = relationship("User", back_populates="sales")
    contact = relationship("Contact")
    status = relationship("SaleStatus")
    outcome = relationship("SalesOutcome")
