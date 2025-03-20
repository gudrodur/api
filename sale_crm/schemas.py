from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# ==========================
# User Schemas
# ==========================

class UserCreate(BaseModel):
    """Schema for user creation"""
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: str = "salesperson"

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==========================
# Contact List Schemas
# ==========================

class ContactCreate(BaseModel):
    """Schema for creating a new contact"""
    name: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True


class ContactResponse(BaseModel):
    """Schema for contact response"""
    id: int
    name: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==========================
# Sales Schemas
# ==========================

class SaleCreate(BaseModel):
    """Schema for creating a new sale"""
    user_id: int
    contact_id: int
    status_id: int
    outcome_id: Optional[int] = None
    sale_amount: float
    payment_status: Optional[str] = None
    expected_closure_date: Optional[datetime] = None  # ✅ Ensure proper datetime handling

    class Config:
        from_attributes = True



class SaleResponse(BaseModel):
    """Schema for sale response"""
    id: int
    user_id: int
    contact_id: int
    status_id: int
    outcome_id: Optional[int] = None
    sale_amount: float
    payment_status: Optional[str] = "Pending"
    expected_closure_date: Optional[datetime] = None
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==========================
# Sale Status Schemas
# ==========================

class SaleStatusCreate(BaseModel):
    """Schema for creating a new sale status"""
    name: str

    class Config:
        from_attributes = True


class SaleStatusResponse(BaseModel):
    """Schema for sale status response"""
    id: int
    name: str

    class Config:
        from_attributes = True

# ==========================
# Sales Outcomes Schemas
# ==========================

class SalesOutcomeCreate(BaseModel):
    """Schema for creating a new sales outcome"""
    description: str

    class Config:
        from_attributes = True


class SalesOutcomeResponse(BaseModel):
    """Schema for sales outcome response"""
    id: int
    description: str

    class Config:
        from_attributes = True

# ==========================
# Call Logs Schemas
# ==========================

class CallCreate(BaseModel):
    """Schema for logging a new call"""
    contact_id: int
    duration: int
    status: str = "pending"  # ✅ Default status
    notes: Optional[str] = None  # ✅ Allow notes

    class Config:
        from_attributes = True


class CallResponse(BaseModel):
    """Schema for retrieving call details"""
    id: int
    user_id: int
    contact_id: int
    duration: int
    call_time: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==========================
# Sale Contacts (Many-to-Many Relationship)
# ==========================

class SaleContactCreate(BaseModel):
    """Schema for linking a sale to a contact"""
    sale_id: int
    contact_id: int

    class Config:
        from_attributes = True


class SaleContactResponse(BaseModel):
    """Schema for retrieving a sale-contact link"""
    id: int
    sale_id: int
    contact_id: int

    class Config:
        from_attributes = True
