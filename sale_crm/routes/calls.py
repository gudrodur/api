from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Optional
import logging

from sale_crm.models import Call, User, Contact, ContactStatus
from sale_crm.schemas import CallCreate, CallOut, CallResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(tags=["Calls"])
logger = logging.getLogger(__name__)

# Mapping between call disposition and contact status
DISPOSITION_TO_CONTACT_STATUS = {
    "SALE": "Closed",
    "CALLBACK": "Follow Up",
    "FOLLOW UP REQUIRED": "Follow Up",
    "INTERESTED": "Follow Up",
    "APPOINTMENT SET": "Follow Up",
    "NOT INTERESTED": "Closed",
    "ANSWERING MACHINE": "Unreachable",
    "BUSY": "Unreachable",
    "UNREACHABLE": "Unreachable",
    "WRONG NUMBER": "Unreachable",
    "DNC": "Do Not Contact",
}

# ----------------------------------------
# Create a New Call
# ----------------------------------------
@router.post("/", response_model=CallResponse, status_code=201)
async def log_call(
    call: CallCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new call log and update contact status based on disposition."""
    contact = await db.get(Contact, call.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    if call.duration < 1:
        raise HTTPException(status_code=400, detail="Call duration must be at least 1 minute.")

    allowed_statuses = {"pending", "completed", "failed", "not interested"}
    if call.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid call status. Allowed: {allowed_statuses}")

    new_call = Call(
        user_id=current_user.id,
        contact_id=call.contact_id,
        duration=call.duration,
        status=call.status,
        notes=call.notes,
        disposition=call.disposition
    )

    try:
        db.add(new_call)
        await db.flush()

        new_status_name = DISPOSITION_TO_CONTACT_STATUS.get(call.disposition)
        if new_status_name:
            result = await db.execute(select(ContactStatus).where(ContactStatus.name == new_status_name))
            status = result.scalars().first()
            if status and contact.status_id != status.id:
                contact.status_id = status.id
                contact.updated_at = datetime.utcnow()
                logger.info(f"Updated contact {contact.id} status to '{new_status_name}' from disposition '{call.disposition}'")

        await db.commit()
        await db.refresh(new_call)

        logger.info(f"Call ID {new_call.id} logged by user {current_user.username} for contact {contact.id}")
        return new_call

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error logging call: {e}")
        raise HTTPException(status_code=400, detail="Database integrity error.")

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error in log_call: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred.")

# ----------------------------------------
# Get All Calls (Admin or Self)
# ----------------------------------------
@router.get("/", response_model=List[CallResponse])
async def get_all_calls(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admins see all calls, users see their own only."""
    stmt = select(Call).options(joinedload(Call.user)) if current_user.role == "admin" \
        else select(Call).where(Call.user_id == current_user.id)

    result = await db.execute(stmt)
    calls = result.scalars().all()

    if not calls:
        raise HTTPException(status_code=404, detail="No calls found.")

    logger.info(f"User {current_user.username} retrieved {len(calls)} call(s).")
    return calls

# ----------------------------------------
# Get Calls by Contact (with optional date filtering)
# ----------------------------------------
@router.get("/contacts/{contact_id}/calls", response_model=List[CallOut])
async def get_calls_by_contact_with_filter(
    contact_id: int,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve call history for a specific contact.
    Supports optional date filtering via `from` and `to` query parameters.
    """
    query = select(Call).where(Call.contact_id == contact_id)
    if from_date:
        query = query.where(Call.created_at >= from_date)
    if to_date:
        query = query.where(Call.created_at <= to_date)

    result = await db.execute(query)
    return result.scalars().all()

# ----------------------------------------
# Get Call by ID
# ----------------------------------------
@router.get("/{call_id}", response_model=CallResponse)
async def get_call_by_id(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a single call by ID. Access restricted to owners or admin."""
    call = await db.get(Call, call_id)
    if not call:
        logger.error(f"Call ID {call_id} not found.")
        raise HTTPException(status_code=404, detail="Call not found.")

    if current_user.role != "admin" and call.user_id != current_user.id:
        logger.warning(f"Unauthorized access to Call ID {call_id} by {current_user.username}")
        raise HTTPException(status_code=403, detail="Permission denied.")

    return call

# ----------------------------------------
# Delete Call by ID
# ----------------------------------------
@router.delete("/{call_id}", status_code=204)
async def delete_call(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a call. Admins or the original user can perform this action."""
    call = await db.get(Call, call_id)
    if not call:
        logger.error(f"Call ID {call_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Call not found.")

    if current_user.role != "admin" and call.user_id != current_user.id:
        logger.warning(f"Unauthorized delete attempt on Call ID {call_id} by {current_user.username}")
        raise HTTPException(status_code=403, detail="Permission denied.")

    try:
        await db.delete(call)
        await db.commit()
        logger.info(f"Call ID {call_id} deleted by {current_user.username}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting call ID {call_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting call.")
