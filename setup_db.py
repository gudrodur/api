from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP, REAL, create_engine
)
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone
from passlib.context import CryptContext

# Database connection
DATABASE_URL = "sqlite:///./phone_sales.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================
# Database Models
# ==========================

class User(Base):
    """Users table"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class ContactList(Base):
    """Contacts table"""
    __tablename__ = "contact_list"
    
    id = Column(Integer, primary_key=True, index=True)
    caller = Column(Integer, default=0)
    socialSecurityNumber = Column(Integer, nullable=True)
    name = Column(String, default="Unknown contact")
    phone = Column(String, nullable=False, unique=True)
    phone2 = Column(String, nullable=True)
    email = Column(String, default="Unknown email")
    age = Column(Integer, default=0)
    googleSheetStatus = Column(String, default="")
    email_verified = Column(Boolean, default=False)
    comment = Column(Text, default="")
    statusCurrent = Column(String, default="Unprocessed")
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    deleted_by = Column(String, nullable=True)


# ==========================
# Database Setup
# ==========================

def drop_tables():
    """Drop tables manually in correct order due to foreign key constraints."""
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys = OFF;")  # ✅ Fixed
        Base.metadata.drop_all(bind=engine)  # Drop all tables
        connection.exec_driver_sql("PRAGMA foreign_keys = ON;")  # ✅ Fixed
    print("Tables dropped successfully!")

def setup_database():
    """Creates all tables and inserts fake data"""
    print("Dropping existing tables...")
    drop_tables()

    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)  # Creates tables
    print("Tables created successfully!")

    db = SessionLocal()

    # Add fake users
    fake_users = [
        User(username="admin", hashed_password=pwd_context.hash("adminpass")),
        User(username="salesperson1", hashed_password=pwd_context.hash("sales123"))
    ]

    # Insert fake data
    db.add_all(fake_users)
    db.commit()
    db.close()

    print("Database setup complete with fake data!")

if __name__ == "__main__":
    setup_database()
