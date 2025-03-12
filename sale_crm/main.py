from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
import os
from sqlalchemy import Column, Integer, String, create_engine
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

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")  # Secret key for JWT encoding/decoding
ALGORITHM = "HS256"  # Algorithm used to sign the JWT token
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Expiration time of the access token

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer extracts the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ==========================
# Database Models
# ==========================

class UserDB(Base):
    """SQLAlchemy User table model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="salesperson")  # Default role is "salesperson"


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
    password: str
    role: str = "salesperson"  # Default role


# ==========================
# API Routes
# ==========================

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Endpoint to create a new user with a unique username"""

    # ✅ Check if the username already exists
    existing_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists! Please choose a different one.")

    # ✅ Hash the password before saving
    hashed_password = hash_password(user.password)  
    db_user = UserDB(username=user.username, hashed_password=hashed_password, role=user.role)

    # ✅ Save to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": f"User {db_user.username} created successfully", "role": db_user.role}


@app.post("/token", response_model=Token)
def login_for_access_token(user: UserCreate, db: Session = Depends(get_db)):
    """Login endpoint to generate JWT token"""
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    
    # Check if the user exists and if the password matches
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")  # Unauthorized access
    
    # Generate an access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected")
def protected_route(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Protected route that requires a valid token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=403, detail="Could not validate credentials")
        
        return {"message": f"Hello, {username}!"}
    
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


@app.get("/admin-only")
def admin_route(user: UserDB = Depends(get_current_user)):
    """Admin-only route"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only!")
    return {"message": "Welcome, admin!"}


@app.delete("/users/{user_id}")
def delete_user(user_id: int, user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    """Admin-only: Delete a user by ID"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only!")

    user_to_delete = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admins from deleting themselves
    if user_to_delete.id == user.id:
        raise HTTPException(status_code=400, detail="Admins cannot delete themselves!")

    db.delete(user_to_delete)
    db.commit()
    return {"message": f"User {user_to_delete.username} deleted successfully."}
