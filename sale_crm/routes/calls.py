from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
import logging
from datetime import datetime
from typing import List

from sale_crm.models import CallDB, UserDB, ContactList
from sale_crm.schemas import CallCreate, CallResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(prefix="/calls", tags=["Calls"])

# ✅ Initialize logger
logger = logging.getLogger(__name__)

# ==========================
# ✅ Create a New Call Log
# ==========================
@router.post("/", response_model=CallResponse, status_code=201)
async def log_call(
    call: CallCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: UserDB = Depends(get_current_user)
):
    """Log a new call with validation."""

    # ✅ Validate contact existence
    contact = await db.get(ContactList, call.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found.")

    # ✅ Validate call duration (should be at least 1 minute)
    if call.duration < 1:
        raise HTTPException(status_code=400, detail="Call duration must be at least 1 minute.")

    # ✅ Validate call status (restrict to valid options)
    allowed_statuses = {"pending", "completed", "failed"}
    if call.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid call status. Allowed: {allowed_statuses}")

    new_call = CallDB(
        user_id=current_user.id,
        contact_id=call.contact_id,
        duration=call.duration,
        status=call.status,
        notes=call.notes
    )

    try:
        db.add(new_call)
        await db.commit()
        await db.refresh(new_call)

        logger.info(f"✅ New call (ID: {new_call.id}) logged by user {current_user.username} for contact {contact.id}")

        return new_call

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError while logging call: {e}")
        raise HTTPException(status_code=400, detail="Database integrity error while logging call.")

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Unexpected Error in log_call: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while logging call.")

# ==========================
# ✅ Get All Calls (Admin & Users)
# ==========================
@router.get("/", response_model=List[CallResponse])
async def get_all_calls(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve call logs. Admins see all calls, users see only their own."""
    if current_user.role == "admin":
        # ✅ Admins can see all calls
        result = await db.execute(select(CallDB).options(joinedload(CallDB.user)))
    else:
        # ✅ Regular users can only see their own calls
        result = await db.execute(select(CallDB).where(CallDB.user_id == current_user.id))

    calls = result.scalars().all()

    if not calls:
        raise HTTPException(status_code=404, detail="No calls found.")

    logger.info(f"🔍 User {current_user.username} retrieved call logs. ({len(calls)} records)")

    return calls

# ==========================
# ✅ Get Call by ID
# ==========================
@router.get("/{call_id}", response_model=CallResponse)
async def get_call_by_id(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve a call log by its ID (Users can only view their own calls, admins can view all)."""

    call = await db.get(CallDB, call_id)

    if not call:
        logger.error(f"❌ Call retrieval failed: Call ID {call_id} not found.")
        raise HTTPException(status_code=404, detail="Call not found.")

    # ✅ Ensure users can only view their own calls unless they are admin
    if current_user.role != "admin" and call.user_id != current_user.id:
        logger.warning(f"⚠️ Unauthorized access attempt on Call ID {call_id} by {current_user.username}.")
        raise HTTPException(status_code=403, detail="You do not have permission to view this call.")

    logger.info(f"🔍 User {current_user.username} accessed Call ID {call_id}.")
    return call

# ==========================
# ✅ Delete a Call Log (Admin or Self)
# ==========================
@router.delete("/{call_id}", status_code=204)
async def delete_call(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Delete a call log (Users can delete their own calls, admins can delete any call)."""

    call = await db.get(CallDB, call_id)

    if not call:
        logger.error(f"❌ Call deletion failed: Call ID {call_id} not found.")
        raise HTTPException(status_code=404, detail="Call not found.")

    # ✅ Ensure users can only delete their own calls unless they are admin
    if current_user.role != "admin" and call.user_id != current_user.id:
        logger.warning(f"⚠️ Unauthorized delete attempt on Call ID {call_id} by {current_user.username}.")
        raise HTTPException(status_code=403, detail="You do not have permission to delete this call.")

    try:
        await db.delete(call)
        await db.commit()

        logger.info(f"✅ Call ID {call_id} deleted by user {current_user.username}.")

        return {"message": "Call deleted successfully"}

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting call ID {call_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while deleting the call.")
