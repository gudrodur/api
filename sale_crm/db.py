from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import logging
from dotenv import load_dotenv
load_dotenv()


# Import models (Ensure Base is imported from models.py to avoid conflicts)
from sale_crm.models.sales import Sale
from sale_crm.models.status_models import SalesOutcome, ContactStatus
from sale_crm.models.users import UserDB
from sale_crm.models.contacts import ContactList


# ==========================
# Load Environment Variables
# ==========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ ERROR: Missing DATABASE_URL! Set it in the environment variables.")

# ==========================
# Configure Logging
# ==========================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# SQLAlchemy Debugging Logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)  # Show SQL queries
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)  # Reduce pool logs in production

# ==========================
# Initialize SQLAlchemy Async Engine
# ==========================
try:
    engine = create_async_engine(DATABASE_URL, echo=(LOG_LEVEL == "DEBUG"))  # Enable SQL logging only in debug mode
    logger.info("✅ Successfully connected to the database!")
except Exception as e:
    logger.critical(f"❌ Failed to connect to the database: {e}")
    sys.exit(1)  # Exit application if DB connection fails

# ==========================
# Async Session Factory
# ==========================
SessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# ==========================
# Dependency to Get DB Session
# ==========================
async def get_db():
    """Dependency function to get an async database session."""
    async with SessionLocal() as db:
        try:
            yield db
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()

# ==========================
# Database Initialization (For Alembic Migrations)
# ==========================
async def init_db():
    """Initialize the database using Alembic (Ensure migrations are applied)."""
    logger.info("🚀 Checking database migrations...")
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)  # ⚠️ Optional: Only use if Alembic is NOT managing migrations
            logger.info("✅ Database schema verified.")
        except Exception as e:
            logger.critical(f"❌ Database migration error: {e}")
            raise

# ==========================
# Optional: Exportable Async Session Maker for Tests
# ==========================
async_session_maker = SessionLocal

