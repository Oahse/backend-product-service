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

class ProductImageBase(BaseModel):
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageRead(ProductImageBase):
    id: str

    class Config:
        from_attributes = True

class ProductVariantBase(BaseModel):
    variant_name: str = Field(..., max_length=100)
    sku: str = Field(..., max_length=100)
    price: condecimal(max_digits=10, decimal_places=2)
    stock: int = 0

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantUpdate(BaseModel):
    variant_name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None

class ProductVariantRead(ProductVariantBase):
    id: str

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
    images: Optional[List[ProductImageCreate]] = []

class ProductRead(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    category: CategoryRead
    tags: List[TagRead] = []
    variants: List[ProductVariantRead] = []
    images: List[ProductImageRead] = []
    inventories: Optional[List[InventoryRead]] = []  # <-- changed from single inventory

    class Config:
        from_attributes = True
