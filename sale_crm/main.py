# ==========================
# Standard Library Imports
# ==========================
import os
from datetime import datetime, timedelta
from typing import Optional, List

from dotenv import load_dotenv
# ==========================
# Third-Party Library Imports
# ==========================

## FastAPI Core
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

## Pydantic for Data Validation
from pydantic import BaseModel, EmailStr, validator

## Authentication & Security
from jose import JWTError, jwt
from passlib.context import CryptContext

## SQLAlchemy ORM & Database Handling
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.future import select
from sqlalchemy.sql.expression import or_
# ==========================
# Load Environment Variables
# ==========================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:adminpass@localhost/phone_sales")

if not SECRET_KEY:
    raise ValueError("❌ ERROR: Missing SECRET_KEY! Set it in the environment variables.")

if not DATABASE_URL:
    raise ValueError("❌ ERROR: Missing DATABASE_URL! Ensure it's correctly set before running the app.")
# ==========================
# Secure Database Connection
# ==========================
engine = create_async_engine(DATABASE_URL, echo=False)  # Set echo=False to avoid logging sensitive data
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()
# ==========================
# Initialize FastAPI Application
# ==========================
app = FastAPI(
    title="Secure Sales CRM API",
    description="This is the API for our Sales CRM system with improved security and performance.",
    version="1.1.0",
    contact={"name": "Support", "email": "support@example.com"},
    openapi_tags=[
        {"name": "Users", "description": "User management operations"},
        {"name": "Sales", "description": "Sales tracking and management"},
    ],
)
# ==========================
# Authentication & Security Settings
# ==========================
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
# ==========================
# Database Models
# ==========================
class UserDB(Base):
    """SQLAlchemy User table model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="salesperson")
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("SaleDB", back_populates="user")


class SaleDB(Base):
    """SQLAlchemy Sales table model"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, nullable=False)
    status_id = Column(Integer, nullable=False)
    outcome_id = Column(Integer, nullable=True)
    sale_amount = Column(Float, nullable=False)
    payment_status = Column(String, nullable=True)
    expected_closure_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserDB", back_populates="sales")
# ==========================
# Pydantic Schemas
# ==========================
class SaleCreate(BaseModel):
    user_id: int
    contact_id: int
    status_id: int
    outcome_id: int
    sale_amount: float
    payment_status: Optional[str] = None
    expected_closure_date: Optional[datetime] = None


class UserUpdate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: str = "salesperson"

    @validator("password")
    def validate_password(cls, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        return password
# ==========================
# Utility Functions
# ==========================
async def get_db():
    async with SessionLocal() as db:
        yield db

def create_access_token(data: dict, expires_delta: timedelta = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
# ==========================
# Authentication Endpoints
# ==========================
@app.post("/auth/token")
async def login_for_access_token(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    result = await db.execute(select(UserDB).where(UserDB.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
# ==========================
# API Routes
# ==========================
@app.post("/users/")
async def create_user(user: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists!")

    hashed_password = hash_password(user.password)
    db_user = UserDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"message": f"User {db_user.username} created successfully", "role": db_user.role}

@app.post("/sales")
async def create_sale(sale: SaleCreate, db: AsyncSession = Depends(get_db)):
    new_sale = SaleDB(**sale.dict())
    db.add(new_sale)
    await db.commit()
    await db.refresh(new_sale)
    return {"message": "Sale created successfully", "sale_id": new_sale.id}
