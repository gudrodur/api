from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List

from sale_crm.models import Contact, ContactStatus, User
from sale_crm.schemas import ContactCreate, ContactResponse, StatusUpdateRequest, UserResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(tags=["Contacts"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    sort_by: str = Query("name", enum=["name", "status_name", "created_at", "updated_at"]),
    order: str = Query("asc", enum=["asc", "desc"]),
    db: AsyncSession = Depends(get_db),
):
    sort_mapping = {
        "name": Contact.name,
        "created_at": Contact.created_at,
        "updated_at": Contact.updated_at,
        "status_name": ContactStatus.name,
    }

    direction = asc if order == "asc" else desc
    sort_column = sort_mapping.get(sort_by, Contact.name)

    query = select(Contact).options(
        joinedload(Contact.status),
        joinedload(Contact.locked_by_user)
    )

    if sort_by == "status_name":
        query = query.join(Contact.status)

    query = query.order_by(direction(sort_column))

    result = await db.execute(query)
    contacts = result.scalars().all()

    response_list = []
    for contact in contacts:
        data = contact.__dict__.copy()
        data.pop("locked_by_user", None)
        data.pop("status", None)

        data["status_name"] = contact.status.name if contact.status else None
        data["user_id"] = contact.locked_by_user_id
        data["locked_by_user"] = (
            UserResponse.model_validate(contact.locked_by_user)
            if contact.locked_by_user else None
        )

        response_list.append(ContactResponse(**data))

    return response_list

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Contact)
        .where(Contact.id == contact_id)
        .options(
            joinedload(Contact.status),
            joinedload(Contact.locked_by_user)
        )
    )
    contact = result.scalar_one_or_none()

    if not contact:
        logger.warning(f"❌ Contact ID {contact_id} not found.")
        raise HTTPException(status_code=404, detail="Contact not found")

    # 🧠 Auto-lock if not already locked
    if contact.locked_by_user_id is None and (contact.status_id == 1):  # status_id == 1 ➜ "New"
        contact.status_id = 2  # status_id == 2 ➜ "Exclusive Lock"
        contact.locked_by_user_id = current_user.id
        contact.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(contact)

        logger.info(f"🔒 Contact ID {contact_id} auto-locked by user '{current_user.username}'.")

    data = contact.__dict__.copy()
    data.pop("locked_by_user", None)
    data.pop("status", None)

    data["status_name"] = contact.status.name if contact.status else None
    data["user_id"] = contact.locked_by_user_id
    data["locked_by_user"] = (
        UserResponse.model_validate(contact.locked_by_user)
        if contact.locked_by_user else None
    )

    return ContactResponse(**data)



class MessageResponse(BaseModel):
    message: str

@router.patch("/{contact_id}/status", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def update_contact_status(
    contact_id: int,
    status_update: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the status of a contact using status_id (recommended)."""
    if status_update.status_id <= 0:
        raise HTTPException(status_code=422, detail="Invalid status ID")

    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact ID {contact_id} not found.")

    result = await db.execute(select(ContactStatus).where(ContactStatus.id == status_update.status_id))
    new_status = result.scalar_one_or_none()
    if not new_status:
        raise HTTPException(status_code=404, detail=f"Status ID {status_update.status_id} not found.")

    contact.status_id = new_status.id
    contact.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(contact)

    logger.info(
        f"✅ User {current_user.username} updated contact {contact_id} to status "
        f"'{new_status.name}' (ID {new_status.id})"
    )

    return {"message": f"Contact {contact_id} status updated successfully."}

@router.get("/locked", response_model=List[ContactResponse])
async def get_locked_contacts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Contact)
        .join(ContactStatus)
        .where(ContactStatus.name == "Exclusive Lock")
        .options(
            joinedload(Contact.status),
            joinedload(Contact.locked_by_user)
        )
    )
    contacts = result.scalars().all()

    response_list = []
    for contact in contacts:
        data = contact.__dict__.copy()
        data.pop("locked_by_user", None)
        data.pop("status", None)

        data["status_name"] = contact.status.name if contact.status else None
        data["user_id"] = contact.locked_by_user_id
        data["locked_by_user"] = (
            UserResponse.model_validate(contact.locked_by_user)
            if contact.locked_by_user else None
        )

        response_list.append(ContactResponse(**data))

    return response_list
