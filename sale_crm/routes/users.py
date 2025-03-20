from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List

from sale_crm.models import UserDB
from sale_crm.schemas import UserCreate, UserResponse
from sale_crm.auth import get_current_user_id, get_current_user, hash_password
from sale_crm.db import get_db

router = APIRouter(prefix="/users", tags=["Users"])

# ==========================
# Create a New User
# ==========================
@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Creates a new user, ensuring username and email are unique."""
    try:
        # Check if username or email already exists
        existing_user = await db.execute(
            select(UserDB).where((UserDB.username == user.username) | (UserDB.email == user.email))
        )
        if existing_user.scalars().first():
            raise HTTPException(status_code=409, detail="Username or email already exists!")

        # Hash password before storing it
        hashed_password = hash_password(user.password)

        db_user = UserDB(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=user.role,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user

    except HTTPException as http_exc:
        # ✅ Ensure the exception is raised properly
        raise http_exc

    except Exception as e:
        # ❌ Log other exceptions and return a 500 error
        print(f"❌ Unexpected Error in create_user: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# ==========================
# Get All Users (Admin Only)
# ==========================
@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    db: AsyncSession = Depends(get_db), 
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve all users (Admin access required)."""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to view all users.")

    result = await db.execute(select(UserDB).options(joinedload(UserDB.sales)))
    return result.scalars().all()

# ==========================
# Get a Single User by ID (Self or Admin)
# ==========================
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id),  # Extract ID from JWT
    current_user: UserDB = Depends(get_current_user)  # Fetch full user details
):
    """Retrieve a user by ID. Admins can view any user, while regular users can only view themselves."""

    # If a regular user tries to access another user's data, deny the request
    if current_user.role != "admin" and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this user.")

    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        phone2=user.phone2,
        last_login=user.last_login,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

# ==========================
# Update User Details (Self or Admin)
# ==========================
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    updated_user: UserCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id),
    current_user: UserDB = Depends(get_current_user)
):
    """Update user details. Users can update themselves, while admins can update anyone."""

    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure users can only update themselves unless they are admin
    if current_user.role != "admin" and current_user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to update this user.")

    # Check if username or email is being changed to an existing one
    existing_user = await db.execute(
        select(UserDB)
        .where((UserDB.username == updated_user.username) | (UserDB.email == updated_user.email))
        .where(UserDB.id != user_id)
    )
    if existing_user.scalars().first():
        raise HTTPException(status_code=409, detail="Username or email is already in use by another user.")

    # Update user fields
    user.username = updated_user.username
    user.email = updated_user.email
    user.full_name = updated_user.full_name
    user.role = updated_user.role

    # Hash new password if provided
    if updated_user.password:
        user.hashed_password = hash_password(updated_user.password)

    await db.commit()
    await db.refresh(user)

    return user

# ==========================
# Delete a User (Self or Admin)
# ==========================
@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id),
    current_user: UserDB = Depends(get_current_user)
):
    """Delete a user. Admins can delete any user, while users can delete themselves."""

    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Ensure users can only delete themselves unless they are admin
    if current_user.role != "admin" and current_user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this user.")

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}
