# ==========================
# Standard Library Imports
# ==========================
import os
from datetime import datetime, timezone

# ==========================
# Third-Party Library Imports
# ==========================

## FastAPI Core
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

## Authentication & Security
from jose import JWTError, jwt
from passlib.context import CryptContext

## SQLAlchemy ORM & Database Handling
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP, REAL
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

from dotenv import load_dotenv
from typing import Optional

from setup_db import SaleDB


# ==========================
# Load Environment Variables
# ==========================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:adminpass@localhost/phone_sales")
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"

# ==========================
# Secure Database Connection
# ==========================
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# ==========================
# Authentication & Security
# ==========================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Function to get the current UTC timestamp
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
# ==========================
# Database Models
# ==========================

class AlembicVersion(Base):
    """Alembic version control table"""
    __tablename__ = "alembic_version"

    version_num = Column(String(32), primary_key=True, nullable=False)


class UserDB(Base):
    """Users table - Manages system users with roles"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(String, default="salesperson")
    last_login = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=utc_now)

    sales = relationship("SaleDB", back_populates="user")
    calls = relationship("CallDB", back_populates="user")


class ContactList(Base):
    """Contacts table - Holds customer contact information"""
    __tablename__ = "contact_list"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=False, unique=True)
    phone2 = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    marketing_consent = Column(Boolean, nullable=True)
    age = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    status_current = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, default=utc_now)
    updated_at = Column(TIMESTAMP, default=utc_now, onupdate=utc_now)

    sales = relationship("SaleDB", back_populates="contact")
    calls = relationship("CallDB", back_populates="contact")


class SaleDB(Base):
    """Sales table - Tracks sales transactions and outcomes"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id"), nullable=False)
    status_id = Column(Integer, ForeignKey("sale_status.id"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("sales_outcomes.id"), nullable=True)
    sale_amount = Column(REAL, nullable=True)
    payment_status = Column(String, nullable=True)
    expected_closure_date = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=utc_now)

    user = relationship("UserDB", back_populates="sales")
    contact = relationship("ContactList", back_populates="sales")
    status = relationship("SaleStatus", back_populates="sales")
    outcome = relationship("SalesOutcome", back_populates="sales")

    print(f"🔍 SaleDB columns in FastAPI: {SaleDB.__table__.columns.keys()}")


class SaleStatus(Base):
    """Sale Status table - Defines the state of a sale (pending, completed, etc.)"""
    __tablename__ = "sale_status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    sales = relationship("SaleDB", back_populates="status")


class SalesOutcome(Base):
    """Sales Outcomes table - Stores possible results of sales (success, failure, etc.)"""
    __tablename__ = "sales_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, unique=True, nullable=False)

    sales = relationship("SaleDB", back_populates="outcome")


class CallDB(Base):
    """Calls table - Logs customer interactions, including status and duration"""
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id"), nullable=False)
    duration = Column(Integer, nullable=False)
    call_type = Column(String, nullable=True)
    outcome = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    call_time = Column(TIMESTAMP, nullable=True)
    recording_url = Column(String, nullable=True)
    call_reason = Column(String, nullable=True)
    agent_feedback = Column(Text, nullable=True)

    user = relationship("UserDB", back_populates="calls")
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
