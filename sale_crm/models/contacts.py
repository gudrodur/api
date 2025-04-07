from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class ContactList(Base):
    __tablename__ = "contact_list"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    phone2 = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    postal_code = Column(Integer, nullable=True)
    region_name = Column(String, nullable=True)
    ssn = Column(String, nullable=True)
    deal_value = Column(Numeric, nullable=True)

    status_id = Column(Integer, ForeignKey("contact_status.id"))
    locked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # 🔗 Relationships
    status = relationship("ContactStatus", back_populates="contacts")
    locked_by_user = relationship("UserDB", back_populates="locked_contacts")
