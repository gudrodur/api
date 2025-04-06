from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List

from sale_crm.models import ContactList, ContactStatus, UserDB
from sale_crm.schemas import ContactCreate, ContactResponse, StatusUpdateRequest, UserResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[ContactResponse])
async def get_contacts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContactList).options(
            joinedload(ContactList.status),
            joinedload(ContactList.locked_by_user)
        )
    )
    contacts = result.scalars().all()

    return [
        ContactResponse(
            **contact.__dict__,
            status_name=contact.status.name if contact.status else None,
            user_id=contact.locked_by_user_id,
            locked_by_user=UserResponse.model_validate(contact.locked_by_user) if contact.locked_by_user else None
        )
        for contact in contacts
    ]


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(contact_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContactList)
        .where(ContactList.id == contact_id)
        .options(
            joinedload(ContactList.status),
            joinedload(ContactList.locked_by_user)
        )
    )
    contact = result.scalars().first()

    if not contact:
        logger.warning(f"❌ Contact ID {contact_id} not found.")
        raise HTTPException(status_code=404, detail="Contact not found")

    return ContactResponse(
        **contact.__dict__,
        status_name=contact.status.name if contact.status else None,
        user_id=contact.locked_by_user_id,
        locked_by_user=UserResponse.model_validate(contact.locked_by_user) if contact.locked_by_user else None
    )


@router.patch("/{contact_id}/status", status_code=204)
async def update_contact_status(
    contact_id: int,
    payload: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    new_status_name = payload.status_name.strip()

    if not new_status_name:
        raise HTTPException(status_code=400, detail="Status name must not be empty.")

    contact = await db.get(ContactList, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    # Check if contact is currently locked
    current_status = None
    if contact.status_id:
        result = await db.execute(select(ContactStatus).where(ContactStatus.id == contact.status_id))
        current_status = result.scalars().first()

    if current_status and current_status.name == "Exclusive Lock" and contact.locked_by_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update status on a locked contact owned by another user."
        )

    # Set new status
    result = await db.execute(select(ContactStatus).where(ContactStatus.name == new_status_name))
    new_status = result.scalars().first()

    if not new_status:
        raise HTTPException(status_code=404, detail=f"Status '{new_status_name}' not found.")

    contact.status_id = new_status.id
    contact.updated_at = datetime.now(timezone.utc)

    if new_status.name == "Exclusive Lock":
        contact.locked_by_user_id = current_user.id
    else:
        contact.locked_by_user_id = None

    await db.commit()
    logger.info(f"✅ Contact {contact.id} status set to '{new_status_name}' by user '{current_user.username}'.")


@router.get("/locked", response_model=List[ContactResponse])
async def get_locked_contacts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContactList)
        .join(ContactStatus)
        .where(ContactStatus.name == "Exclusive Lock")
        .options(
            joinedload(ContactList.status),
            joinedload(ContactList.locked_by_user)
        )
    )
    contacts = result.scalars().all()

    return [
        ContactResponse(
            **contact.__dict__,
            status_name=contact.status.name if contact.status else None,
            user_id=contact.locked_by_user_id,
            locked_by_user=UserResponse.model_validate(contact.locked_by_user) if contact.locked_by_user else None
        )
        for contact in contacts
    ]
