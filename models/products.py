from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Text, BigInteger, Table, DECIMAL
from core.database import Base, CHAR_LENGTH
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any
from models.category import Category
from models.inventory import Inventory
from models.tag import Tag

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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "category_id": self.category_id,
            "category": self.category.to_dict() if self.category else None,
            "tags": [tag.to_dict() for tag in self.tags] if self.tags else [],
            "base_price": float(self.base_price),
            "sale_price": float(self.sale_price) if self.sale_price else None,
            "availability": self.availability.name if self.availability else None,
            "rating": float(self.rating) if self.rating else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "variants": [variant.to_dict() for variant in self.variants] if self.variants else [],
            "images": [image.to_dict() for image in self.images] if self.images else [],
            # If you want inventory dict representation:
            "inventory": self.inventory.to_dict() if self.inventory else None,
        }

    def __repr__(self):
        return f"<Product(id={self.id!r}, name={self.name!r}, sku={self.sku!r})>"
class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    product: Mapped["Product"] = relationship("Product", back_populates="variants")

    variant_name: Mapped[str] = mapped_column(String(100), index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), index=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "variant_name": self.variant_name,
            "sku": self.sku,
            "price": float(self.price),
            "stock": self.stock,
        }

    def __repr__(self):
        return f"<ProductVariant(id={self.id!r}, variant_name={self.variant_name!r}, sku={self.sku!r})>"


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    product: Mapped["Product"] = relationship("Product", back_populates="images")

    url: Mapped[str] = mapped_column(Text, index=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(CHAR_LENGTH), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "url": self.url,
            "alt_text": self.alt_text,
            "is_primary": self.is_primary,
        }

    def __repr__(self):
        return f"<ProductImage(id={self.id!r}, url={self.url!r}, is_primary={self.is_primary})>"
