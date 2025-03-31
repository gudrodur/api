from datetime import datetime, timezone
import logging
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional

from sale_crm.models import ContactList, ContactStatus, CallDB, UserDB
from sale_crm.schemas import ContactCreate, ContactResponse, CallResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(prefix="/contacts", tags=["Contacts"])
logger = logging.getLogger(__name__)


# ==========================
# ✅ Get all contacts
# ==========================
@router.get("/", response_model=List[ContactResponse])
async def get_contacts(db: AsyncSession = Depends(get_db)):
    """Retrieve all contacts with status name"""
    result = await db.execute(select(ContactList).options(joinedload(ContactList.status)))
    contacts = result.scalars().all()

    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found")

    # Manually map status name into response
    response = []
    for contact in contacts:
        contact_data = ContactResponse.model_validate(contact)
        contact_data.status_name = contact.status.name if contact.status else None
        response.append(contact_data)

    return response


# ==========================
# ✅ Create a new contact
# ==========================
@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    """Create a new contact"""
    normalized_phone = contact.phone.strip()
    normalized_email = contact.email.strip().lower() if contact.email else None

    existing_contact = await db.execute(
        select(ContactList).filter(
            (ContactList.phone == normalized_phone) |
            (ContactList.email == normalized_email)
        )
    )

    if existing_contact.scalars().first():
        raise HTTPException(status_code=400, detail="Phone or email already exists.")

    new_contact = ContactList(
        name=contact.name,
        phone=normalized_phone,
        phone2=contact.phone2,
        email=normalized_email,
        address=contact.address,
        postal_code=contact.postal_code,
        region_name=contact.region_name,
        ssn=contact.ssn,
        status_id=contact.status_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    try:
        db.add(new_contact)
        await db.commit()
        await db.refresh(new_contact)
        return ContactResponse.model_validate(new_contact)
    except IntegrityError as e:
        await db.rollback()
        error_message = str(e.orig)
        logger.error(f"❌ Database IntegrityError: {error_message}")

        if "contact_list_phone_key" in error_message:
            raise HTTPException(status_code=400, detail="Phone number already exists.")
        elif "contact_list_email_key" in error_message:
            raise HTTPException(status_code=400, detail="Email already registered.")
        elif "contact_list_ssn_key" in error_message:
            raise HTTPException(status_code=400, detail="SSN already registered.")
        else:
            raise HTTPException(status_code=400, detail="An error occurred while creating the contact.")


# ==========================
# ✅ Update an existing contact
# ==========================
@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    """Update an existing contact"""
    contact_db = await db.get(ContactList, contact_id)
    if not contact_db:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact_db.name = contact.name or contact_db.name
    contact_db.phone = contact.phone or contact_db.phone
    contact_db.phone2 = contact.phone2 or contact_db.phone2
    contact_db.email = contact.email or contact_db.email
    contact_db.address = contact.address or contact_db.address
    contact_db.postal_code = contact.postal_code or contact_db.postal_code
    contact_db.region_name = contact.region_name or contact_db.region_name
    contact_db.ssn = contact.ssn or contact_db.ssn
    contact_db.status_id = contact.status_id or contact_db.status_id
    contact_db.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(contact_db)
        return ContactResponse.model_validate(contact_db)
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ Update Error: {e}")
        raise HTTPException(status_code=400, detail="An error occurred while updating the contact.")


# ==========================
# ✅ Delete a contact
# ==========================
@router.delete("/{contact_id}", status_code=204)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a contact by ID"""
    contact_db = await db.get(ContactList, contact_id)
    if not contact_db:
        raise HTTPException(status_code=404, detail="Contact not found")

    try:
        await db.delete(contact_db)
        await db.commit()
        return {"message": "Contact deleted successfully"}
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Delete Error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while deleting the contact.")


# ==========================
# ✅ Get single contact by ID
# ==========================
@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a single contact by its ID"""
    result = await db.execute(
        select(ContactList).where(ContactList.id == contact_id).options(joinedload(ContactList.status))
    )
    contact = result.scalars().first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact_data = ContactResponse.model_validate(contact)
    contact_data.status_name = contact.status.name if contact.status else None
    return contact_data


# ==========================
# ✅ Get All Calls for a Contact ID
# ==========================
@router.get("/contact/{contact_id}", response_model=List[CallResponse])
async def get_calls_by_contact_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve all call logs for a contact"""
    stmt = select(CallDB).where(CallDB.contact_id == contact_id)

    if current_user.role != "admin":
        stmt = stmt.where(CallDB.user_id == current_user.id)

    result = await db.execute(stmt)
    calls = result.scalars().all()

    logger.info(f"📞 {len(calls)} call(s) fetched for contact ID {contact_id} by user {current_user.username}")
    return calls
