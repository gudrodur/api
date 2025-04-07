from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .base import Base  # Sameinaðar Base-týpur

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="salesperson", nullable=False)

    phone = Column(String, nullable=True)
    phone2 = Column(String, nullable=True)

    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # 🔗 Relationships (Sale, Call, Contact, SaleContact)
    locked_contacts = relationship("Contact", back_populates="locked_by_user")
    calls = relationship("Call", back_populates="user")
    sales = relationship("Sale", back_populates="user")
    sale_contacts_created = relationship("SaleContact", back_populates="created_by_user")
