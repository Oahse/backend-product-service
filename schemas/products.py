from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from pydantic import BaseModel, Field, condecimal


class AvailabilityStatus(str, PyEnum):
    IN_STOCK = "In Stock"
    OUT_OF_STOCK = "Out of Stock"
    PREORDER = "Preorder"


class TagBase(BaseModel):
    name: str = Field(..., max_length=100)

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: str

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: str

    class Config:
        from_attributes = True


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
    price: Optional[float] = None
    stock: Optional[int] = None
class ProductVariantRead(ProductVariantBase):
    id: str

    class Config:
        from_attributes = True


class InventoryBase(BaseModel):
    quantity: int = 0
    low_stock_threshold: int = 5

class InventoryCreate(InventoryBase):
    pass

class InventoryRead(InventoryBase):
    id: str

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str = Field(..., max_length=100)
    sku: str = Field(..., max_length=100)
    description: Optional[str] = None
    base_price: condecimal(max_digits=10, decimal_places=2)
    sale_price: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    availability: AvailabilityStatus = AvailabilityStatus.IN_STOCK
    rating: Optional[condecimal(max_digits=2, decimal_places=1)] = 0.0
    category_id: str
    tag_ids: Optional[List[int]] = []

class ProductCreate(ProductBase):
    variants: Optional[List[ProductVariantCreate]] = []
    images: Optional[List[ProductImageCreate]] = []
    inventory: Optional[InventoryCreate] = None

class ProductRead(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    category: CategoryRead
    tags: List[TagRead] = []
    variants: List[ProductVariantRead] = []
    images: List[ProductImageRead] = []
    inventory: Optional[InventoryRead] = None

    class Config:
        from_attributes = True


class PromoCodeBase(BaseModel):
    code: str = Field(..., max_length=50)
    discount_percent: condecimal(max_digits=5, decimal_places=2)
    active: bool = True
    valid_from: datetime
    valid_until: datetime

class PromoCodeCreate(PromoCodeBase):
    pass

class PromoCodeRead(PromoCodeBase):
    id: str

    class Config:
        from_attributes = True
