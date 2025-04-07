from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
import logging
from datetime import datetime
from typing import List, Optional

from sale_crm.models import SaleDB, UserDB, ContactList, SaleStatus, SalesOutcomes
from sale_crm.schemas import SaleCreate, SaleResponse
from sale_crm.db import get_db
from sale_crm.auth import get_current_user

router = APIRouter(tags=["Sales"])

# ✅ Initialize logger
logger = logging.getLogger(__name__)

# ==========================
# ✅ Create a New Sale
# ==========================
@router.post("/", response_model=SaleResponse)
async def create_sale(
    sale: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Creates a new sale after validating user, contact, and status."""
    try:
        # ✅ Validate user existence
        user = await db.get(UserDB, sale.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # ✅ Validate contact existence
        contact = await db.get(ContactList, sale.contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found.")

        # ✅ Validate sale status
        status = await db.get(SaleStatus, sale.status_id)
        if not status:
            raise HTTPException(status_code=404, detail="Sale status not found.")

        # ✅ Validate outcome (if provided)
        if sale.outcome_id:
            outcome = await db.get(SalesOutcomes, sale.outcome_id)
            if not outcome:
                raise HTTPException(status_code=404, detail="Sale outcome not found.")

        # ✅ Prevent duplicate sales
        existing_sale = await db.execute(
            select(SaleDB)
            .where(SaleDB.user_id == sale.user_id, SaleDB.contact_id == sale.contact_id)
        )
        if existing_sale.scalars().first():
            raise HTTPException(status_code=409, detail="A sale already exists for this user and contact.")

        # ✅ Validate sale amount (ensure non-negative values)
        if sale.sale_amount < 0:
            raise HTTPException(status_code=400, detail="Sale amount cannot be negative.")

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

        logger.info(f"✅ Sale {new_sale.id} created by user {current_user.username}.")

        return new_sale

    except HTTPException as http_exc:
        await db.rollback()
        raise http_exc  # Keep existing HTTPExceptions

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"❌ IntegrityError: {e}")
        raise HTTPException(status_code=400, detail="Database integrity error while creating sale.")

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Unexpected Error in create_sale: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating sale.")

# ==========================
# ✅ Get All Sales (Admin Only)
# ==========================
@router.get("/", response_model=List[SaleResponse])
async def get_all_sales(
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve all sales (Admin access required)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to view all sales.")

    result = await db.execute(
        select(SaleDB).options(joinedload(SaleDB.user), joinedload(SaleDB.contact))
    )
    sales = result.scalars().all()

    logger.info(f"Admin {current_user.username} retrieved all sales.")
    return sales

# ==========================
# ✅ Get a Sale by ID
# ==========================
@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale_by_id(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Retrieve a sale by its ID (Users can only view their own sales, admins can view all)."""
    sale = await db.get(SaleDB, sale_id)

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")

    if current_user.role != "admin" and sale.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this sale.")

    return sale

# ==========================
# ✅ Update a Sale
# ==========================
@router.put("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: int,
    updated_sale: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Update sale details (Users can update their own sales, admins can update any sale)."""
    sale = await db.get(SaleDB, sale_id)

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")

    if current_user.role != "admin" and sale.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to update this sale.")

    # ✅ Validate sale amount
    if updated_sale.sale_amount < 0:
        raise HTTPException(status_code=400, detail="Sale amount cannot be negative.")

    sale.contact_id = updated_sale.contact_id
    sale.status_id = updated_sale.status_id
    sale.outcome_id = updated_sale.outcome_id
    sale.sale_amount = updated_sale.sale_amount
    sale.payment_status = updated_sale.payment_status
    sale.expected_closure_date = updated_sale.expected_closure_date

    await db.commit()
    await db.refresh(sale)

    logger.info(f"✅ Sale ID {sale.id} updated by {current_user.username}.")
    return sale

# ==========================
# ✅ Delete a Sale
# ==========================
@router.delete("/{sale_id}")
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Delete a sale (Users can delete their own sales, admins can delete any sale)."""
    sale = await db.get(SaleDB, sale_id)

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")

    if current_user.role != "admin" and sale.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this sale.")

    await db.delete(sale)
    await db.commit()

    logger.info(f"✅ Sale ID {sale_id} deleted by {current_user.username}.")
    return {"message": "Sale deleted successfully"}
