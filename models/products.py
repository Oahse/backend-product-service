from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Text, BigInteger, Table, DECIMAL
from core.database import Base, CHAR_LENGTH
from core.utils.encryption import PasswordManager
from core.utils.generator import generator
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import UUID

# Many-to-many association table
product_tags = Table(
    "product_tags",
    Base.metadata,
    mapped_column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True, index=True),
    mapped_column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True),
)

class AvailabilityStatus(PyEnum):
    IN_STOCK = "In Stock"
    OUT_OF_STOCK = "Out of Stock"
    PREORDER = "Preorder"

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }

    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, name={self.name!r})"

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, index=False)  # Usually text fields are not indexed

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r})"

class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, index=False)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    category: Mapped["Category"] = relationship("Category")

    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=product_tags, backref="products")

    base_price: Mapped[float] = mapped_column(DECIMAL(10, 2), index=False)
    sale_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True, index=False)

    availability: Mapped[AvailabilityStatus] = mapped_column(Enum(AvailabilityStatus), default=AvailabilityStatus.IN_STOCK, index=True)

    rating: Mapped[Optional[float]] = mapped_column(DECIMAL(2, 1), default=0.0, index=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    inventory: Mapped["Inventory"] = relationship("Inventory", uselist=False, back_populates="product", cascade="all, delete-orphan")

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    product: Mapped["Product"] = relationship("Product", back_populates="variants")

    variant_name: Mapped[str] = mapped_column(String(100), index=True)  # Often searched/filter on variant name
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), index=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, index=True)  # Stock can be filtered

class Inventory(Base):
    __tablename__ = "inventories"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True)
    product: Mapped["Product"] = relationship("Product", back_populates="inventory")

    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, index=True)

class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    product: Mapped["Product"] = relationship("Product", back_populates="images")

    url: Mapped[str] = mapped_column(Text, index=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(CHAR_LENGTH), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_percent: Mapped[float] = mapped_column(DECIMAL(5, 2), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, index=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "discount_percent": float(self.discount_percent),
            "active": self.active,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None
        }
