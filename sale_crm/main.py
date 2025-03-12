# ==========================
# Standard Library Imports
# ==========================
import os
from datetime import datetime, timedelta

# ==========================
# Third-Party Library Imports
# ==========================

## FastAPI Core
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

## Pydantic for Data Validation
from pydantic import BaseModel, EmailStr

## Authentication & Security
from jose import JWTError, jwt
from passlib.context import CryptContext

## SQLAlchemy ORM & Database Handling
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

# ==========================
# Database Connection
# ==========================

DATABASE_URL = "postgresql+asyncpg://postgres:adminpass@localhost/phone_sales"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

# ==========================
# Initialize FastAPI Application
# ==========================

app = FastAPI(
    title="My Sales CRM API",
    description="This is the API for our Sales CRM system.",
    version="1.0.0",
    contact={
        "name": "Support",
        "email": "support@example.com",
    },
    openapi_tags=[
        {"name": "Users", "description": "Operations related to users"},
        {"name": "Sales", "description": "Operations related to sales"},
    ],
)

# ==========================
# Authentication Settings
# ==========================

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# ==========================
# Database Models
# ==========================

class UserDB(Base):
    """SQLAlchemy User table model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default="salesperson")  # Default role is "salesperson"
    created_at = Column(DateTime, default=datetime.utcnow)

# ==========================
# Utility Functions
# ==========================

async def get_db():
    """Dependency to get the database session"""
    async with SessionLocal() as db:
        yield db


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Function to create a JWT token"""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password, hashed_password):
    """Verifies a plaintext password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str):
    """Hashes a password using bcrypt"""
    return pwd_context.hash(password)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid token")

        result = await db.execute(select(UserDB).where(UserDB.username == username))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


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


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    email: EmailStr
    full_name: str

# ==========================
# API Routes
# ==========================

@app.post("/users/")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).filter((UserDB.username == user.username) | (UserDB.email == user.email)))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists!")

    hashed_password = hash_password(user.password)
    db_user = UserDB(
        username=user.username, email=user.email, full_name=user.full_name, hashed_password=hashed_password, role=user.role
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return {"message": f"User {db_user.username} created successfully", "role": db_user.role}


@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Endpoint to update user profile (email & full_name)"""

    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only update your own profile")

    db_user.full_name = user_data.full_name
    db_user.email = user_data.email
    await db.commit()
    await db.refresh(db_user)

    return {"message": "User profile updated successfully"}
