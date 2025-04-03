from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()

# ==========================
# Call Table
# ==========================
class CallDB(Base):
    __tablename__ = "calls"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id", ondelete="CASCADE"), nullable=False)
    duration = Column(Integer, nullable=False)
    call_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String, default="pending", nullable=False)
    disposition = Column(String(50), nullable=True)  # ✅ Nýr dálkur til að halda utan um "disposition"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("UserDB", back_populates="calls")
    contact = relationship("ContactList", back_populates="calls")



# ==========================
# Contact Status Table
# ==========================
class ContactStatus(Base):
    __tablename__ = "contact_status"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)

    contacts = relationship("ContactList", back_populates="status", cascade="all, delete-orphan")


# ==========================
# Contact List Table
# ==========================
class ContactList(Base):
    """SQLAlchemy Contact List table model"""
    __tablename__ = "contact_list"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    phone = Column(String(20), nullable=False, unique=True)  # ✅ Added length constraint
    phone2 = Column(String(20), nullable=True)  # ✅ Added length constraint
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    postal_code = Column(Integer, nullable=True)
    region_name = Column(String(50), nullable=True)
    ssn = Column(String(12), unique=True, nullable=True)  # ✅ Added length constraint
    deal_value = Column(Float, nullable=True)  # 💰
    status_id = Column(Integer, ForeignKey("contact_status.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    status = relationship("ContactStatus", back_populates="contacts")
    sales = relationship("SaleDB", back_populates="contact", cascade="all, delete-orphan")
    calls = relationship("CallDB", back_populates="contact", cascade="all, delete-orphan")
    sale_contacts = relationship("SaleContact", back_populates="contact", cascade="all, delete-orphan")


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
    phone = Column(String(20), nullable=True)  # ✅ Added length constraint
    phone2 = Column(String(20), nullable=True)  # ✅ Added length constraint
    last_login = Column(DateTime(timezone=True), nullable=True)
    role = Column(String, default="salesperson", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    sales = relationship("SaleDB", back_populates="user", cascade="all, delete-orphan")
    calls = relationship("CallDB", back_populates="user", cascade="all, delete-orphan")


# ==========================
# Sales Table
# ==========================
class SaleDB(Base):
    """SQLAlchemy Sales table model"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id", ondelete="CASCADE"), nullable=False)
    status_id = Column(Integer, ForeignKey("sale_status.id", ondelete="CASCADE"), nullable=False)
    outcome_id = Column(Integer, ForeignKey("sales_outcomes.id", ondelete="SET NULL"), nullable=True)
    sale_amount = Column(Float, nullable=False)
    payment_status = Column(String, nullable=True)
    expected_closure_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("UserDB", back_populates="sales")
    contact = relationship("ContactList", back_populates="sales")
    status = relationship("SaleStatus", back_populates="sales")
    outcome = relationship("SalesOutcomes", back_populates="sales")

    sale_contacts = relationship("SaleContact", back_populates="sale", cascade="all, delete-orphan")


# ==========================
# Sale Status Table
# ==========================
class SaleStatus(Base):
    """SQLAlchemy Sale Status table model"""
    __tablename__ = "sale_status"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    sales = relationship("SaleDB", back_populates="status", cascade="all, delete-orphan")


# ==========================
# Sales Outcomes Table
# ==========================
class SalesOutcomes(Base):
    """SQLAlchemy Sales Outcomes table model"""
    __tablename__ = "sales_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)

    sales = relationship("SaleDB", back_populates="outcome", cascade="all, delete-orphan")

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

