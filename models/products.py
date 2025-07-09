from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Text, DECIMAL, Table, Column
from core.database import Base, CHAR_LENGTH
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Dict, Any
from models.category import Category
from models.tag import Tag

# --- Association table for many-to-many relationship ---
product_tags = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True),
)

# --- Enum for product availability ---
class AvailabilityStatus(PyEnum):
    IN_STOCK = "In Stock"
    OUT_OF_STOCK = "Out of Stock"
    PREORDER = "Preorder"

# --- Product Model ---
class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    category_id: Mapped[Optional[str]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    category: Mapped[Optional["Category"]] = relationship("Category")

    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=product_tags, backref="products")

    base_price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    sale_price: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)

    availability: Mapped[AvailabilityStatus] = mapped_column(Enum(AvailabilityStatus), default=AvailabilityStatus.IN_STOCK, index=True)

    rating: Mapped[Optional[float]] = mapped_column(DECIMAL(2, 1), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    inventory_products: Mapped[List["InventoryProduct"]] = relationship(
        "InventoryProduct", back_populates="product", cascade="all, delete-orphan"
    )
    inventories: Mapped[List["Inventory"]] = relationship(
        "Inventory",
        secondary="inventory_products",
        back_populates="products",
        viewonly=True,
    )
    
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category_id": self.category_id,
            "category": self.category.name if self.category else None,
            "tags": [tag.to_dict() for tag in self.tags],
            "base_price": float(self.base_price),
            "sale_price": float(self.sale_price) if self.sale_price else None,
            "availability": self.availability.value if self.availability else None,
            "rating": float(self.rating) if self.rating else 0.0,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "variants": [v.to_dict() for v in self.variants],
            "images": [img.to_dict() for img in self.images],
            "inventories": [inv.to_dict() for inv in self.inventories],
        }

    def __repr__(self):
        return f"<Product(id={self.id!r}, name={self.name!r}, category={self.category!r})>"

# --- ProductVariant Model ---
class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    product: Mapped["Product"] = relationship("Product", back_populates="variants")

    variant_name: Mapped[str] = mapped_column(String(100), index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)

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

# --- ProductImage Model ---
class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    product: Mapped["Product"] = relationship("Product", back_populates="images")

    url: Mapped[str] = mapped_column(Text)
    alt_text: Mapped[Optional[str]] = mapped_column(String(CHAR_LENGTH))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

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

# --- Inventory Model ---
class Inventory(Base):
    __tablename__ = "inventories"
    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(200))

    inventory_products: Mapped[List["InventoryProduct"]] = relationship(
        "InventoryProduct", back_populates="inventory", cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product",
        secondary="inventory_products",
        back_populates="inventories",
        viewonly=True,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "products": [ip.product.to_dict() for ip in self.inventory_products],
            "product_counts": {ip.product_id: ip.quantity for ip in self.inventory_products}
        }

class InventoryProduct(Base):
    __tablename__ = "inventory_products"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    inventory_id: Mapped[str] = mapped_column(ForeignKey("inventories.id"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=0)  # optional

    inventory: Mapped["Inventory"] = relationship("Inventory", back_populates="inventory_products")
    product: Mapped["Product"] = relationship("Product", back_populates="inventory_products")

    def to_dict(self):
        return {
            "inventory_id": self.inventory_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "low_stock_threshold": self.low_stock_threshold,
        }
