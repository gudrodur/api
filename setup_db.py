import os
import sys
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Ensure the correct import path for sale_crm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:adminpass@localhost/phone_sales")
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

def get_base():
    """Lazy-load models from sale_crm.main to avoid circular import issues"""
    try:
        from sale_crm.main import UserDB, SaleDB, ContactList, SaleStatus, CallDB, SalesOutcomes  # 👈 Fix import path
        return Base
    except ModuleNotFoundError as e:
        print(f"❌ Error: {e}. Ensure that 'sale_crm/main.py' is inside the correct directory and is importable.")
        raise
