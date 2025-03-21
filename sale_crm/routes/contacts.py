from datetime import datetime, timezone
import logging
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from sale_crm.models import ContactList
from sale_crm.schemas import ContactCreate, ContactResponse
from sale_crm.db import get_db

router = APIRouter(prefix="/contacts", tags=["Contacts"])

# ✅ Configure Logging
logger = logging.getLogger(__name__)


# ==========================
# ✅ Get all contacts
# ==========================
@router.get("/", response_model=List[ContactResponse])
async def get_contacts(db: AsyncSession = Depends(get_db)):
    """Retrieve all contacts"""
    result = await db.execute(select(ContactList))
    contacts = result.scalars().all()

    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found")

    return contacts


# ==========================
# ✅ Create a new contact
# ==========================
@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db)):
    """Create a new contact"""
    # Check for existing phone or email before creating
    existing_contact = await db.execute(select(ContactList).filter(
        (ContactList.phone == contact.phone) | 
        (ContactList.email == contact.email)
    ))
    if existing_contact.scalars().first():
        raise HTTPException(status_code=400, detail="Phone or email already exists.")

    new_contact = ContactList(
        name=contact.name,
        phone=contact.phone,
        phone2=contact.phone2,
        email=contact.email,
        address=contact.address,
        postal_code=contact.postal_code,
        region_name=contact.region_name,
        ssn=contact.ssn,
        created_at=datetime.now(timezone.utc),  # ✅ Use UTC timezone
        updated_at=datetime.now(timezone.utc),
    )

    try:
        db.add(new_contact)
        await db.commit()
        await db.refresh(new_contact)
        return new_contact

    except IntegrityError as e:
        await db.rollback()
        error_message = str(e.orig)
        logger.error(f"❌ Database IntegrityError: {error_message}")

        if "phone_format" in error_message:
            raise HTTPException(status_code=400, detail="Invalid phone number format (must be 7-20 digits, optional + at start).")
        elif "phone2_format" in error_message:
            raise HTTPException(status_code=400, detail="Invalid secondary phone number format (must be 7-20 digits, optional + at start).")
        elif "contact_list_phone_key" in error_message:
            raise HTTPException(status_code=400, detail="Phone number already exists.")
        elif "contact_list_ssn_key" in error_message:
            raise HTTPException(status_code=400, detail="SSN already registered.")
        elif "contact_list_email_key" in error_message:
            raise HTTPException(status_code=400, detail="Email already registered.")
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

    # Update fields only if provided
    contact_db.name = contact.name or contact_db.name
    contact_db.phone = contact.phone or contact_db.phone
    contact_db.phone2 = contact.phone2 or contact_db.phone2
    contact_db.email = contact.email or contact_db.email
    contact_db.address = contact.address or contact_db.address
    contact_db.postal_code = contact.postal_code or contact_db.postal_code
    contact_db.region_name = contact.region_name or contact_db.region_name
    contact_db.ssn = contact.ssn or contact_db.ssn
    contact_db.updated_at = datetime.now(timezone.utc)  # ✅ Update timestamp

    try:
        await db.commit()
        await db.refresh(contact_db)
        return contact_db

    except IntegrityError as e:
        await db.rollback()
        error_message = str(e.orig)
        logger.error(f"❌ Update Error: {error_message}")
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
