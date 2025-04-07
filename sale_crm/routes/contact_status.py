from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
import logging
from typing import List

from sale_crm.models import ContactStatus, ContactStatusEnum, UserDB
from sale_crm.schemas import ContactStatusCreate, ContactStatusResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(tags=["Contact Status"])
logger = logging.getLogger(__name__)


# ==========================
# ✅ Create a New Contact Status
# ==========================
@router.post("/", response_model=ContactStatusResponse, status_code=201)
async def create_contact_status(
    status: ContactStatusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Create a new contact status (Admins only). Enforces enum compliance."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create contact statuses.")

    status_name = status.name.strip()

    # ✅ Check enum compliance (must match one of ContactStatusEnum values)
    if status_name not in [e.value for e in ContactStatusEnum]:
        raise HTTPException(
            status_code=422,
            detail=f"Status '{status_name}' is not allowed. Valid values: {', '.join(e.value for e in ContactStatusEnum)}"
        )

    existing_status = await db.execute(select(ContactStatus).where(ContactStatus.name == status_name))
    if existing_status.scalars().first():
        raise HTTPException(status_code=400, detail=f"Contact status '{status_name}' already exists.")

    new_status = ContactStatus(name=status_name)

    try:
        db.add(new_status)
        await db.commit()
        await db.refresh(new_status)

        logger.info(f"✅ Contact status '{status_name}' created by admin {current_user.username}.")
        return new_status

    except IntegrityError:
        await db.rollback()
        logger.error(f"❌ IntegrityError: Duplicate status '{status_name}'.")
        raise HTTPException(status_code=400, detail="Duplicate contact status.")

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Unexpected Error in create_contact_status: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


# ==========================
# ✅ Get All Contact Statuses
# ==========================
@router.get("/", response_model=List[ContactStatusResponse])
async def get_all_contact_statuses(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve all contact statuses."""
    result = await db.execute(select(ContactStatus))
    statuses = result.scalars().all()

    if not statuses:
        raise HTTPException(status_code=404, detail="No contact statuses found.")

    logger.info(f"🔍 User {current_user.username} retrieved {len(statuses)} contact statuses.")
    return statuses
