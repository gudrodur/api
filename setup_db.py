from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP, REAL
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# ==========================
# Database Connection - PostgreSQL
# ==========================
DATABASE_URL = "postgresql+asyncpg://postgres:adminpass@localhost/phone_sales"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# ==========================
# Database Models
# ==========================

class User(Base):
    """Users table - Manages system users with roles"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)  # Optional: Store agent's phone
    role = Column(String, default="salesperson")  # Default role is "salesperson"
    last_login = Column(TIMESTAMP, nullable=True)  # Last login time
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    sales = relationship("Sale", back_populates="user")
    calls = relationship("Call", back_populates="user")


class ContactList(Base):
    """Contacts table - Holds customer contact information"""
    __tablename__ = "contact_list"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Unknown contact")
    phone = Column(String, nullable=False, unique=True)
    phone2 = Column(String, nullable=True)
    email = Column(String, default="Unknown email")
    address = Column(String, nullable=True)  # Address of the customer
    gender = Column(String, nullable=True)  # "Male", "Female", "Other"
    nationality = Column(String, nullable=True)
    marketing_consent = Column(Boolean, default=False)  # Marketing opt-in
    age = Column(Integer, default=0)
    comment = Column(Text, default="")
    status_current = Column(String, default="Unprocessed")
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sales = relationship("Sale", back_populates="contact")
    calls = relationship("Call", back_populates="contact")


class Sale(Base):
    """Sales table - Tracks sales transactions and outcomes"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("sale_status.id"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("sales_outcomes.id"), nullable=True)
    sale_amount = Column(REAL, nullable=True)
    payment_status = Column(String, default="pending")  # New field: pending, paid, refunded
    expected_closure_date = Column(TIMESTAMP, nullable=True)  # New field: expected closing date
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="sales")
    contact = relationship("ContactList", back_populates="sales")
    status = relationship("SaleStatus", back_populates="sales")
    outcome = relationship("SalesOutcome", back_populates="sales")


class SaleStatus(Base):
    """Sale Status table - Defines the state of a sale (pending, completed, etc.)"""
    __tablename__ = "sale_status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    sales = relationship("Sale", back_populates="status")


class SalesOutcome(Base):
    """Sales Outcomes table - Stores possible results of sales (success, failure, etc.)"""
    __tablename__ = "sales_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, unique=True, nullable=False)

    sales = relationship("Sale", back_populates="outcome")


class Call(Base):
    """Calls table - Logs customer interactions, including status and duration"""
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id"), nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in seconds
    call_type = Column(String, default="outbound")  # New field: inbound or outbound
    outcome = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    call_time = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    recording_url = Column(String, nullable=True)  # New field: Link to recording
    call_reason = Column(String, nullable=True)  # New field: Reason for call
    agent_feedback = Column(Text, nullable=True)  # New field: Agent's remarks

    user = relationship("User", back_populates="calls")
    contact = relationship("ContactList", back_populates="calls")


class SaleContact(Base):
    """Sale Contacts table - Links contacts to sales for relationship tracking"""
    __tablename__ = "sale_contacts"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id"), nullable=False)


# ==========================
# Database Setup
# ==========================

async def reset_database():
    """Drops and recreates all tables."""
    async with engine.begin() as conn:
        print("Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database reset complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(reset_database())
