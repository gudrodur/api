from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

# ==========================
# User Table
# ==========================
class UserDB(Base):
    """SQLAlchemy User table model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    phone2 = Column(String, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)  # ✅ Timezone-aware
    role = Column(String, default="salesperson", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # ✅ Ensure this relationship exists
    sales = relationship("SaleDB", back_populates="user", cascade="all, delete")
    calls = relationship("CallDB", back_populates="user", cascade="all, delete")

# ==========================
# Contact List Table
# ==========================
class ContactList(Base):
    """SQLAlchemy Contact List table model"""
    __tablename__ = "contact_list"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # ✅ Ensure this relationship exists
    sales = relationship("SaleDB", back_populates="contact", cascade="all, delete")
    calls = relationship("CallDB", back_populates="contact", cascade="all, delete") 
    sale_contacts = relationship("SaleContact", back_populates="contact", cascade="all, delete")  # ✅ ADD THIS

# ==========================
# Sales Table
# ==========================
class SaleDB(Base):
    """SQLAlchemy Sales table model"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id", ondelete="CASCADE"), nullable=False)
    status_id = Column(Integer, ForeignKey("sale_status.id"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("sales_outcomes.id", ondelete="SET NULL"), nullable=True)
    sale_amount = Column(Float, nullable=False)
    payment_status = Column(String, nullable=True)
    expected_closure_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # ✅ Ensure this relationship exists
    user = relationship("UserDB", back_populates="sales")
    contact = relationship("ContactList", back_populates="sales")
    status = relationship("SaleStatus", back_populates="sales")
    outcome = relationship("SalesOutcomes", back_populates="sales")

    sale_contacts = relationship("SaleContact", back_populates="sale", cascade="all, delete")  # ✅ ADD THIS

# ==========================
# Sale Status Table
# ==========================
class SaleStatus(Base):
    """SQLAlchemy Sale Status table model"""
    __tablename__ = "sale_status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    sales = relationship("SaleDB", back_populates="status")

# ==========================
# Sales Outcomes Table
# ==========================
class SalesOutcomes(Base):
    """SQLAlchemy Sales Outcomes table model"""
    __tablename__ = "sales_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)

    sales = relationship("SaleDB", back_populates="outcome")

# ==========================
# Call Logs Table
# ==========================
class CallDB(Base):
    """SQLAlchemy Call Logs table model"""
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id", ondelete="CASCADE"), nullable=False)
    duration = Column(Integer, nullable=False)
    call_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String, default="pending", nullable=False)  # ✅ Call status (completed, failed, pending)
    notes = Column(Text, nullable=True)  # ✅ Additional call details
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("UserDB", back_populates="calls")
    contact = relationship("ContactList", back_populates="calls")

# ==========================
# Sale Contact Table (Many-to-Many Relationship)
# ==========================
class SaleContact(Base):
    """SQLAlchemy table linking sales to contacts"""
    __tablename__ = "sale_contacts"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id", ondelete="CASCADE"), nullable=False)

    sale = relationship("SaleDB", back_populates="sale_contacts")
    contact = relationship("ContactList", back_populates="sale_contacts")

