from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from sale_crm.db import get_db
from sale_crm.models import UserDB

# ==========================
# ✅ Load Environment Variables
# ==========================
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    sys.exit("❌ ERROR: Missing SECRET_KEY! Set it in the environment variables.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7  # ✅ Added refresh token expiration

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ✅ Add FastAPI Router
router = APIRouter(prefix="/auth", tags=["Authentication"])

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
    """Authenticate user and return JWT access token."""
    result = await db.execute(select(UserDB).where(UserDB.username == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # ✅ Store user ID in the token payload
    access_token = create_access_token(user_id=user.id)

    # ✅ Return ID in response JSON
    return {
        "id": user.id,
        "access_token": access_token,
        "token_type": "bearer"
    }

# ==========================
# ✅ User Authentication & Retrieval
# ==========================
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Retrieve the current logged-in user using the user ID from the token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid token")

        user_id = int(user_id)  # ✅ Ensure user ID is converted properly

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
        user_id = payload.get("sub")  # ✅ Ensure `sub` is stored as string

        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid token")

        # ✅ Convert `sub` to integer safely
        try:
            return int(user_id)
        except ValueError:
            raise HTTPException(status_code=403, detail="Token contains invalid user ID")

    except JWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")