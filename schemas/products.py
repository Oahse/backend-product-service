from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, condecimal
from schemas.category import CategoryRead
from schemas.tag import TagRead
from schemas.inventory import InventoryRead

class AvailabilityStatus(str, PyEnum):
    IN_STOCK = "In Stock"
    OUT_OF_STOCK = "Out of Stock"
    PREORDER = "Preorder"

# --- Variant Attribute ---
class ProductVariantAttributeBase(BaseModel):
    name: str
    value: str

class ProductVariantAttributeCreate(ProductVariantAttributeBase):
    pass

class ProductVariantAttributeRead(ProductVariantAttributeBase):
    id: str

    class Config:
        from_attributes = True

# --- Variant Image ---
class ProductVariantImageBase(BaseModel):
    url: str

class ProductVariantImageCreate(ProductVariantImageBase):
    pass

class ProductVariantImageRead(ProductVariantImageBase):
    id: str
    variant_id: str

    class Config:
        from_attributes = True

class ProductVariantBase(BaseModel):
    price: float
    stock: int = 0
    variant_name: str


# --- Create ---
class ProductVariantCreate(ProductVariantBase):
    attributes: Optional[List[ProductVariantAttributeCreate]] = []
    images: Optional[List[ProductVariantImageCreate]] = []


# --- Update ---
class ProductVariantUpdate(BaseModel):
    price: Optional[float]
    stock: Optional[int]
    attributes: Optional[List[ProductVariantAttributeCreate]] = []
    images: Optional[List[ProductVariantImageCreate]] = []


# --- Read / Response ---
class ProductVariantRead(ProductVariantBase):
    id: str
    product_id: str
    attributes: List[ProductVariantAttributeRead] = []
    images: List[ProductVariantImageRead] = []

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    base_price: condecimal(max_digits=10, decimal_places=2)
    sale_price: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    availability: AvailabilityStatus = AvailabilityStatus.IN_STOCK
    rating: Optional[condecimal(max_digits=2, decimal_places=1)] = 0.0
    category_id: str
    tag_ids: Optional[List[str]] = []
    inventory_ids: Optional[List[str]] = []  # <-- changed from inventory_id

class ProductCreate(ProductBase):
    variants: Optional[List[ProductVariantCreate]] = []

class ProductRead(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    category: CategoryRead
    tags: List[TagRead] = []
    variants: List[ProductVariantRead] = []
    inventories: Optional[List[InventoryRead]] = []  # <-- changed from single inventory

    class Config:
        from_attributes = True
