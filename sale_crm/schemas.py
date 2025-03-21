import re
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timezone
from typing import Optional


# ==========================
# Contact Status Schemas
# ==========================
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
    password: str  # ✅ Added to match DB (will be hashed)
    hashed_password: Optional[str] = None  # ✅ Ensure compatibility
    role: str = "salesperson"
    phone: Optional[str] = None
    phone2: Optional[str] = None

    @field_validator("phone", "phone2")
    @classmethod
    def validate_phone(cls, v):
        """Ensure phone numbers contain only digits and optional '+' prefix."""
        if v and not re.match(r"^\+?\d{7,20}$", v):
            raise ValueError("Phone number must contain 7-20 digits and may start with '+'.")
        return v


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    phone: Optional[str] = None
    phone2: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================
# Contact List Schemas
# ==========================
class ContactCreate(BaseModel):
    """Schema for creating a new contact"""
    name: Optional[str] = None
    phone: str
    phone2: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    postal_code: Optional[int] = None
    region_name: Optional[str] = None
    ssn: Optional[str] = None
    status_id: Optional[int] = None

    @field_validator("phone", "phone2")
    @classmethod
    def validate_phone(cls, v):
        """Ensure phone numbers contain only digits and optional '+' prefix."""
        if v and not re.match(r"^\+?\d{7,20}$", v):
            raise ValueError("Phone number must contain 7-20 digits and may start with '+'.")
        return v

    @field_validator("ssn")
    @classmethod
    def validate_ssn(cls, v):
        """Ensure SSN follows Icelandic format (YYYYMM-DDDD or YYYYMMDDDD)."""
        if v and not re.match(r"^\d{6}-?\d{4}$", v):
            raise ValueError("SSN must be in the format YYYYMM-DDDD or YYYYMMDDDD.")
        return v


class ContactResponse(ContactCreate):
    """Schema for contact response"""
    id: int
    created_at: datetime
    updated_at: datetime

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
    payment_status: Optional[str] = "Pending"
    expected_closure_date: Optional[datetime] = None


class SaleResponse(SaleCreate):
    """Schema for sale response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================
# Sale Status Schemas
# ==========================
class SaleStatusCreate(BaseModel):
    """Schema for creating a new sale status"""
    name: str


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
    user_id: int
    contact_id: int
    duration: int
    call_time: Optional[datetime] = None
    status: Optional[str] = "pending"
    notes: Optional[str] = None


class CallResponse(CallCreate):
    """Schema for retrieving call details"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================
# Sale Contacts (Many-to-Many Relationship)
# ==========================
class SaleContactCreate(BaseModel):
    """Schema for linking a sale to a contact"""
    sale_id: int
    contact_id: int


class SaleContactResponse(BaseModel):
    """Schema for retrieving a sale-contact link"""
    id: int
    sale_id: int
    contact_id: int

    class Config:
        from_attributes = True
