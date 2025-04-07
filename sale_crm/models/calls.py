from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    contact_id = Column(Integer, ForeignKey("contact_list.id"))

    duration = Column(Integer, nullable=True)
    disposition = Column(String, nullable=True)
    status = Column(String, nullable=True, default="pending")           # 🆕
    notes = Column(String, nullable=True)                               # 🆕
    call_time = Column(DateTime(timezone=True), nullable=True)          # 🆕

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # 🔗 Relationships
    user = relationship("User", back_populates="calls")
    contact = relationship("Contact")
