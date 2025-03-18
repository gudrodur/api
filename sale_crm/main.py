# ==========================
# Standard Library Imports
# ==========================
import os
from datetime import datetime, timedelta

# ==========================
# Third-Party Library Imports
# ==========================

## FastAPI Core
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

## Pydantic for Data Validation
from pydantic import BaseModel, EmailStr, validator

## Authentication & Security
from jose import JWTError, jwt
from passlib.context import CryptContext

## SQLAlchemy ORM & Database Handling
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import or_

from dotenv import load_dotenv

from typing import Optional, List

# ==========================
# Load Environment Variables
# ==========================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not SECRET_KEY:
    raise ValueError("❌ ERROR: Missing SECRET_KEY! Set it in the environment variables.")

if not DATABASE_URL:
    raise ValueError("❌ ERROR: Missing DATABASE_URL! Ensure it's correctly set before running the app.")

# ==========================
# Secure Database Connection
# ==========================
engine = create_async_engine(DATABASE_URL, echo=False)  # Set echo=False to avoid logging sensitive data
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

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

# Define a Pydantic model for incoming sales data
class SaleCreate(BaseModel):
    contact_id: int
    sales_outcome: str
    sales_amount: float
    remarks: Optional[str] = None

# In-memory storage for demo purposes
sales_db = []

# ==========================
# Utility Functions
# ==========================

async def get_db():
    """Dependency to get the database session"""
    async with SessionLocal() as db:
        yield db

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generate a JWT access token with an expiration time"""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """Generate a refresh token with a longer expiration time"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a password securely using bcrypt"""
    return pwd_context.hash(password)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Retrieve the current logged-in user from the JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=403, detail="Invalid token")

        result = await db.execute(select(UserDB).where(UserDB.username == username))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

# ==========================
# Authentication Endpoints
# ==========================

@app.post("/auth/token")
async def login_for_access_token(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return a JWT token."""
    result = await db.execute(select(UserDB).where(UserDB.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================
# Pydantic Schemas
# ==========================

class UserCreate(BaseModel):
    """Schema for creating a user"""
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: str = "salesperson"

    @validator("password")
    def validate_password(cls, password):
        """Ensure strong password rules"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        return password

# ==========================
# API Routes
# ==========================

@app.post("/users/")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Create a new user - Restricted to Admins Only"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users.")

    result = await db.execute(select(UserDB).where(or_(UserDB.username == user.username, UserDB.email == user.email)))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username or email already exists!")

    hashed_password = hash_password(user.password)
    db_user = UserDB(username=user.username, email=user.email, full_name=user.full_name, hashed_password=hashed_password, role=user.role)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"message": f"User {db_user.username} created successfully", "role": db_user.role}

@app.get("/users/me")
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Fetch the currently authenticated user's information."""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }

@app.post("/sales")
def create_sale(sale: SaleCreate):
    # In a real app, you would save to a database
    new_sale = sale.dict()
    sales_db.append(new_sale)
    return {
        "message": "Sale created successfully",
        "sale": new_sale
    }

@app.get("/sales")
def get_all_sales():
    return sales_db
