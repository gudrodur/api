from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class SaleContact(Base):
    __tablename__ = "sale_contacts"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # 🔗 Relationships
    sale = relationship("Sale")
    contact = relationship("Contact")
    created_by_user = relationship("User", back_populates="sale_contacts_created")
