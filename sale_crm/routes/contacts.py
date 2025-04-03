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
    """Retrieve all contacts with their status name."""
    result = await db.execute(select(ContactList).options(joinedload(ContactList.status)))
    contacts = result.scalars().all()

    if not contacts:
        raise HTTPException(status_code=404, detail="No contacts found")

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
    """Create a new contact."""
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
        deal_value=contact.deal_value,
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
    """Update an existing contact."""
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
    contact_db.deal_value = contact.deal_value if contact.deal_value is not None else contact_db.deal_value
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
    """Delete a contact by ID."""
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
# ✅ Get a single contact by ID
# ==========================
@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a single contact by its ID."""
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
# ✅ API alias for Android: GET /contacts/contact/{id}
# ==========================
@router.get("/contact/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id_alias(contact_id: int, db: AsyncSession = Depends(get_db)):
    """Alias to retrieve contact by ID (for Android)."""
    return await get_contact_by_id(contact_id, db)


# ==========================
# ✅ Get all calls for a contact
# ==========================
@router.get("/contact/{contact_id}/calls", response_model=List[CallResponse])
async def get_calls_by_contact_id(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve all call logs for a contact."""
    stmt = select(CallDB).where(CallDB.contact_id == contact_id)

    if current_user.role != "admin":
        stmt = stmt.where(CallDB.user_id == current_user.id)

    result = await db.execute(stmt)
    calls = result.scalars().all()

    logger.info(f"📞 {len(calls)} call(s) fetched for contact ID {contact_id} by user {current_user.username}")
    return calls


# ==========================
# ✅ Set status to "In Progress" from "New"
# ==========================
@router.patch("/{contact_id}/set-in-progress", status_code=204)
async def set_contact_in_progress(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    result = await db.execute(select(ContactList).where(ContactList.id == contact_id))
    contact = result.scalars().first()

    if not contact:
        logger.error(f"❌ Contact {contact_id} not found for PATCH /set-in-progress")
        raise HTTPException(status_code=404, detail="Contact not found")

    result = await db.execute(select(ContactStatus).where(ContactStatus.id == contact.status_id))
    current_status = result.scalars().first()

    if current_status and current_status.name not in {"Closed", "Do Not Contact", "In Progress"}:
        result = await db.execute(select(ContactStatus).where(ContactStatus.name == "In Progress"))
        in_progress = result.scalars().first()

        if in_progress:
            contact.status_id = in_progress.id
            contact.updated_at = datetime.utcnow()
            await db.commit()
            logger.info(f"🟡 Contact {contact.id} auto-updated to 'In Progress' by {current_user.username}")

    return


# ==========================
# ✅ Revert status to "New" from "In Progress"
# ==========================
@router.patch("/{contact_id}/set-to-new", status_code=204)
async def revert_to_new(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    result = await db.execute(select(ContactList).where(ContactList.id == contact_id))
    contact = result.scalars().first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    result = await db.execute(select(ContactStatus).where(ContactStatus.id == contact.status_id))
    current_status = result.scalars().first()

    if current_status and current_status.name == "In Progress":
        result = await db.execute(select(ContactStatus).where(ContactStatus.name == "New"))
        new_status = result.scalars().first()

        if new_status:
            contact.status_id = new_status.id
            contact.updated_at = datetime.utcnow()
            await db.commit()
            logger.info(f"🔁 Contact {contact.id} status reverted to 'New' by {current_user.username}")
        return

    raise HTTPException(status_code=409, detail="Contact status is not 'In Progress'; cannot revert to 'New'")
