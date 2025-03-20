from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import sys
import logging
# Import all models BEFORE initializing the database
from sale_crm.models import UserDB, SaleDB, ContactList, SaleStatus, SalesOutcomes, CallDB

# ==========================
# Load Environment Variables
# ==========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    sys.exit("❌ ERROR: Missing DATABASE_URL! Set it in the environment variables.")

# ==========================
# Configure Logging for Debugging
# ==========================
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# SQLAlchemy Debugging Logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)  # Fyrir SQL fyrirspurnir
logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)   # Fyrir database connection pool logs

# ==========================
# Initialize SQLAlchemy Async Engine
# ==========================
engine = create_async_engine(DATABASE_URL, echo=True)  # `echo=True` sýnir SQL fyrirspurnir í terminal

SessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# ==========================
# Base Model for Migrations
# ==========================
Base = declarative_base()

# ==========================
# Dependency to Get DB Session
# ==========================
async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
        except Exception as e:
            logger.error(f"Database error: {e}")
            await db.rollback()
            raise  # Important: Raise the error instead of suppressing it
        finally:
            await db.close()

# ==========================
# Database Initialization (For Alembic Migrations)
# ==========================
async def init_db():
    """Ensure the database tables are created on startup"""
    logger.info("🚀 Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # ✅ Ensures all tables are created
    logger.info("✅ Database initialized successfully!")
