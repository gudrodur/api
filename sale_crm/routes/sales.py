from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
import logging
from datetime import datetime
import traceback

from sale_crm.models import SaleDB, UserDB, ContactList, SaleStatus, SalesOutcomes
from sale_crm.schemas import SaleCreate, SaleResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(prefix="/sales", tags=["Sales"])

# Initialize logger
logger = logging.getLogger(__name__)

# ==========================
# Create a New Sale
# ==========================
@router.post("/", response_model=SaleResponse)
async def create_sale(
    sale: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Creates a new sale after validating user, contact, and status."""
    try:
        # Validate user existence
        result = await db.execute(select(UserDB).where(UserDB.id == sale.user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Validate contact existence
        result = await db.execute(select(ContactList).where(ContactList.id == sale.contact_id))
        contact = result.scalars().first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found.")

        # Validate sale status
        result = await db.execute(select(SaleStatus).where(SaleStatus.id == sale.status_id))
        status = result.scalars().first()
        if not status:
            raise HTTPException(status_code=404, detail="Sale status not found.")

        # Validate outcome (if provided)
        outcome = None
        if sale.outcome_id:
            result = await db.execute(select(SalesOutcomes).where(SalesOutcomes.id == sale.outcome_id))
            outcome = result.scalars().first()
            if not outcome:
                raise HTTPException(status_code=404, detail="Sale outcome not found.")

        # ✅ No need for manual datetime conversion (Pydantic does it)
        new_sale = SaleDB(
            user_id=sale.user_id,
            contact_id=sale.contact_id,
            status_id=sale.status_id,
            outcome_id=sale.outcome_id,
            sale_amount=sale.sale_amount,
            payment_status=sale.payment_status,
            expected_closure_date=sale.expected_closure_date,
        )

        db.add(new_sale)
        await db.commit()
        await db.refresh(new_sale)

        return new_sale

    except HTTPException as http_exc:
        raise http_exc  # Keep existing HTTPExceptions
    except Exception as e:
        error_message = f"Error creating sale: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=error_message)

# ==========================
# Get All Sales (Admin Only)
# ==========================
@router.get("/", response_model=List[SaleResponse])
async def get_all_sales(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve all sales (Admin access required)."""
    if current_user.role != "admin":
        logger.warning(f"Unauthorized access attempt by {current_user.username}.")
        raise HTTPException(status_code=403, detail="You do not have permission to view all sales.")

    result = await db.execute(
        select(SaleDB).options(joinedload(SaleDB.user), joinedload(SaleDB.contact))
    )
    sales = result.scalars().all()

    logger.info(f"Admin {current_user.username} retrieved all sales.")
    return sales

# ==========================
# Get a Sale by ID
# ==========================
@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale_by_id(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve a sale by its ID (Users can only view their own sales, admins can view all)."""
    result = await db.execute(select(SaleDB).where(SaleDB.id == sale_id))
    sale = result.scalars().first()

    if not sale:
        logger.error(f"Sale retrieval failed: Sale ID {sale_id} not found.")
        raise HTTPException(status_code=404, detail="Sale not found.")

    if current_user.role != "admin" and sale.user_id != current_user.id:
        logger.warning(f"Unauthorized access attempt on Sale ID {sale_id} by {current_user.username}.")
        raise HTTPException(status_code=403, detail="You do not have permission to view this sale.")

    logger.info(f"User {current_user.username} accessed Sale ID {sale_id}.")
    return sale

# ==========================
# Update a Sale
# ==========================
@router.put("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: int,
    updated_sale: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Update sale details (Users can update their own sales, admins can update any sale)."""
    result = await db.execute(select(SaleDB).where(SaleDB.id == sale_id))
    sale = result.scalars().first()

    if not sale:
        logger.error(f"Sale update failed: Sale ID {sale_id} not found.")
        raise HTTPException(status_code=404, detail="Sale not found.")

    if current_user.role != "admin" and sale.user_id != current_user.id:
        logger.warning(f"Unauthorized update attempt on Sale ID {sale_id} by {current_user.username}.")
        raise HTTPException(status_code=403, detail="You do not have permission to update this sale.")

    # ✅ Ensure all fields are updated
    sale.contact_id = updated_sale.contact_id
    sale.status_id = updated_sale.status_id
    sale.outcome_id = updated_sale.outcome_id
    sale.sale_amount = updated_sale.sale_amount
    sale.payment_status = updated_sale.payment_status
    sale.expected_closure_date = updated_sale.expected_closure_date

    await db.commit()
    await db.refresh(sale)

    logger.info(f"Sale ID {sale.id} updated by user {current_user.username}.")
    return sale

# ==========================
# Delete a Sale
# ==========================
@router.delete("/{sale_id}")
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Delete a sale (Users can delete their own sales, admins can delete any sale)."""
    result = await db.execute(select(SaleDB).where(SaleDB.id == sale_id))
    sale = result.scalars().first()

    if not sale:
        logger.error(f"Sale deletion failed: Sale ID {sale_id} not found.")
        raise HTTPException(status_code=404, detail="Sale not found.")

    if current_user.role != "admin" and sale.user_id != current_user.id:
        logger.warning(f"Unauthorized delete attempt on Sale ID {sale_id} by {current_user.username}.")
        raise HTTPException(status_code=403, detail="You do not have permission to delete this sale.")

    await db.delete(sale)
    await db.commit()

    logger.info(f"Sale ID {sale_id} deleted by user {current_user.username}.")
    return {"message": "Sale deleted successfully"}
