import re
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
from typing import Optional

# ==========================
# Contact Status Schemas
# ==========================

# Optional: Enum for known statuses (not enforced, but can be used for frontend validation)
class ContactStatusName(str, Enum):
    active = "Active"
    in_progress = "In Progress"
    completed = "Completed"
    follow_up = "Follow Up"
    blocked = "Blocked"
    wrong_nr = "Wrong Nr"

class ContactStatusCreate(BaseModel):
    name: str

class ContactStatusResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ==========================
# User Schemas
# ==========================
class UserCreate(BaseModel):
    """Schema for user creation"""
    username: str
    email: EmailStr
    full_name: str
    password: str  # ✅ Password should not be pre-hashed!
    role: str = "salesperson"
    phone: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")
    phone2: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    phone: Optional[str] = None
    phone2: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True


# ==========================
# Contact List Schemas
# ==========================
class ContactCreate(BaseModel):
    """Schema for creating a new contact"""
    name: Optional[str] = None
    phone: str = Field(..., min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")
    phone2: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    postal_code: Optional[int] = None
    region_name: Optional[str] = None
    ssn: Optional[str] = Field(None, pattern=r"^\d{6}-?\d{4}$")
    status_id: Optional[int] = None


class ContactResponse(ContactCreate):
    """Schema for contact response"""
    id: int
    status_name: Optional[str] = None  # ✅ Show readable status (e.g. "Active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    payment_status: Optional[str] = Field(default="Pending")
    expected_closure_date: Optional[datetime] = None


class SaleResponse(SaleCreate):
    """Schema for sale response"""
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True


# ==========================
# Call Logs Schemas
# ==========================
class CallCreate(BaseModel):
    """Schema for logging a new call"""
    user_id: int
    contact_id: int
    duration: int
    call_time: Optional[datetime] = None
    status: str = Field(default="pending")
    notes: Optional[str] = None
    disposition: Optional[str] = None  # ✅ New optional field


class CallResponse(CallCreate):
    """Schema for retrieving call details"""
    id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True
