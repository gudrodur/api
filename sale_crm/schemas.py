from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ==========================
# Contact Status Enum
# ==========================
class ContactStatusName(str, Enum):
    new = "New"
    exclusive_lock = "Exclusive Lock"
    follow_up = "Follow Up"
    closed = "Closed"
    unreachable = "Unreachable"
    do_not_contact = "Do Not Contact"

# ==========================
# Contact Status Schemas
# ==========================
class ContactStatusCreate(BaseModel):
    name: str


class ContactStatusResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

# ==========================
# User Schemas
# ==========================
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: str = "salesperson"
    phone: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")
    phone2: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")


class UserResponse(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)

# ==========================
# Contact Schemas
# ==========================
class ContactCreate(BaseModel):
    name: Optional[str] = None
    phone: str = Field(..., min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")
    phone2: Optional[str] = Field(None, min_length=7, max_length=20, pattern=r"^\+?\d{7,20}$")
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    postal_code: Optional[int] = None
    region_name: Optional[str] = None
    ssn: Optional[str] = Field(None, pattern=r"^\d{6}-?\d{4}$")
    status_id: Optional[int] = None
    deal_value: Optional[float] = None


class ContactResponse(ContactCreate):
    id: int
    status_name: Optional[str] = None
    user_id: Optional[int] = None
    locked_by_user: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================
# Status Update
# ==========================
class StatusUpdateRequest(BaseModel):
    status_name: ContactStatusName

# ==========================
# Sales Schemas
# ==========================
class SaleCreate(BaseModel):
    user_id: int
    contact_id: int
    status_id: int
    outcome_id: Optional[int] = None
    sale_amount: float
    payment_status: Optional[str] = Field(default="Pending")
    expected_closure_date: Optional[datetime] = None


class SaleResponse(SaleCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================
# Call Logs Schemas
# ==========================
class CallCreate(BaseModel):
    user_id: int
    contact_id: int
    duration: int
    call_time: Optional[datetime] = None
    status: str = Field(default="pending")
    notes: Optional[str] = None
    disposition: Optional[str] = None


class CallResponse(BaseModel):
    id: int
    user_id: int
    contact_id: int
    duration: Optional[int] = None
    disposition: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    call_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CallOut(BaseModel):
    id: int
    user_id: int
    contact_id: int
    duration: int
    disposition: Optional[str]
    status: str
    notes: Optional[str]
    call_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


