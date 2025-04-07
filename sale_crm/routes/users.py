from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
import logging
from typing import List, Optional

from sale_crm.models import UserDB
from sale_crm.schemas import UserCreate, UserResponse
from sale_crm.auth import get_current_user_id, get_current_user, hash_password
from sale_crm.db import get_db

router = APIRouter(tags=["Users"])

logger = logging.getLogger(__name__)

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing_user = await db.execute(
            select(UserDB).where(
                (UserDB.username == user.username) |
                (UserDB.email == user.email) |
                (UserDB.phone == user.phone) |
                (UserDB.phone2 == user.phone2)
            )
        )
        if existing_user.scalars().first():
            raise HTTPException(status_code=409, detail="Username, email, or phone number already exists!")

        hashed_password = hash_password(user.password)
        db_user = UserDB(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=user.role,
            phone=user.phone,
            phone2=user.phone2
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError: {str(e.orig)}")
        raise HTTPException(status_code=400, detail="Failed to create user due to database constraints.")

    except Exception as e:
        logger.error(f"❌ Unexpected Error in create_user: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/", response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to view all users.")
    result = await db.execute(select(UserDB).options(joinedload(UserDB.sales)))
    return result.scalars().all()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id), current_user: UserDB = Depends(get_current_user)):
    if current_user.role != "admin" and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this user.")
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, updated_user: UserCreate, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id), current_user: UserDB = Depends(get_current_user)):
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role != "admin" and current_user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to update this user.")
    existing_user = await db.execute(
        select(UserDB)
        .where((UserDB.username == updated_user.username) | (UserDB.email == updated_user.email))
        .where(UserDB.id != user_id)
    )
    if existing_user.scalars().first():
        raise HTTPException(status_code=409, detail="Username or email is already in use by another user.")

    user.username = updated_user.username
    user.email = updated_user.email
    user.full_name = updated_user.full_name
    user.role = updated_user.role
    user.phone = updated_user.phone
    user.phone2 = updated_user.phone2
    if updated_user.password:
        user.hashed_password = hash_password(updated_user.password)

    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError on update: {e}")
        raise HTTPException(status_code=400, detail="Failed to update user due to database constraints.")

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user_id: int = Depends(get_current_user_id), current_user: UserDB = Depends(get_current_user)):
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role != "admin" and current_user_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this user.")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}