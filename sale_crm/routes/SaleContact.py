# ==========================
# Sale Contact Table (Many-to-Many Relationship)
# ==========================
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship  # ✅ Import relationship
from sale_crm.models import Base


class SaleContact(Base):
    """SQLAlchemy table linking sales to contacts"""
    __tablename__ = "sale_contacts"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact_list.id", ondelete="CASCADE"), nullable=False)

    sale = relationship("SaleDB", back_populates="sale_contacts")
    contact = relationship("ContactList", back_populates="sale_contacts")
