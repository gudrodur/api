from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
import sys
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from sale_crm.db import get_db
from sale_crm.models import UserDB

# ==========================
# ✅ Load Environment Variables
# ==========================
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # ✅ Configurable
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))  # ✅ Configurable
ALGORITHM = "HS256"

if not SECRET_KEY:
    sys.exit("❌ ERROR: Missing SECRET_KEY! Set it in the environment variables.")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ✅ Add FastAPI Router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ✅ Initialize logger
logger = logging.getLogger(__name__)

# ==========================
# ✅ Password Hashing & Verification
# ==========================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a password securely."""
    return pwd_context.hash(password)

# ==========================
# ✅ JWT Token Management
# ==========================
def create_access_token(user_id: int, expires_delta: timedelta = None) -> str:
    """Generate a JWT access token with user ID."""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": str(user_id), "exp": expire}  # ✅ Ensure `sub` stores user ID as string
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    """Generate a JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "exp": expire}  # ✅ Store user ID as string
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==========================
# ✅ Authentication Endpoint (Token)
# ==========================
@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT access & refresh tokens."""
    result = await db.execute(select(UserDB).where(UserDB.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"❌ Failed login attempt for username: {form_data.username}")
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # ✅ Update last login time
    user.last_login = datetime.utcnow()
    await db.commit()

    # ✅ Generate access & refresh tokens
    access_token = create_access_token(user_id=user.id)
    refresh_token = create_refresh_token(user_id=user.id)

    logger.info(f"✅ User {user.username} logged in successfully.")

    return {
        "id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# ==========================
# ✅ Refresh Token Endpoint
# ==========================
@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str, db: AsyncSession = Depends(get_db)
):
    """Refresh access token using a valid refresh token."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))

        result = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # ✅ Generate a new access token
        new_access_token = create_access_token(user_id=user.id)
        return {"access_token": new_access_token, "token_type": "bearer"}

    except JWTError:
        logger.warning("❌ Invalid refresh token attempt")
        raise HTTPException(status_code=403, detail="Could not validate refresh token")

# ==========================
# ✅ User Authentication & Retrieval
# ==========================
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Retrieve the current logged-in user using the user ID from the token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))

        result = await db.execute(select(UserDB).where(UserDB.id == user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Retrieve only the user ID from the JWT token without a database lookup."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid token")

        return int(user_id)  # ✅ Convert to integer safely

    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
