from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base
from enum import Enum

class ContactStatusEnum(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ContactStatus(Base):
    __tablename__ = "contact_status"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    contacts = relationship("Contact", back_populates="status")


class SaleStatus(Base):
    __tablename__ = "sale_status"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)


class SalesOutcome(Base):
    __tablename__ = "sales_outcomes"
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)

