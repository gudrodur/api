from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
import os
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext

# ==========================
# Database Connection
# ==========================

DATABASE_URL = "sqlite:///./phone_sales.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ==========================
# Initialize FastAPI Application
# ==========================

app = FastAPI()

# ==========================
# Authentication Settings
# ==========================

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def get_db():
    """Dependency to get the database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Extract user info from JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user = db.query(UserDB).filter(UserDB.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

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
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Endpoint to create a new user with a unique username"""

    existing_user = db.query(UserDB).filter((UserDB.username == user.username) | (UserDB.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists!")

    hashed_password = hash_password(user.password)
    db_user = UserDB(
        username=user.username, email=user.email, full_name=user.full_name, hashed_password=hashed_password, role=user.role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": f"User {db_user.username} created successfully", "role": db_user.role}

@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    """Endpoint to update user profile (email & full_name)"""

    # Check if user exists
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the current user is allowed to update this profile
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only update your own profile")

    # Update fields
    db_user.full_name = user_data.full_name
    db_user.email = user_data.email
    db.commit()
    db.refresh(db_user)

    return {"message": "User profile updated successfully"}