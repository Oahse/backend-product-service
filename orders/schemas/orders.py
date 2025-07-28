from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    Pending = "Pending"
    Processing = "Processing"
    Shipped = "Shipped"
    Delivered = "Delivered"
    Cancelled = "Cancelled"
    Returned = "Returned"
    Failed = "Failed"


class OrderItemSchema(BaseModel):
    product_id: str
    quantity: int
    price_per_unit: float
    total_price: Optional[float]

    class Config:
        from_attributes = True


class OrderSchema(BaseModel):
    user_id: str
    status: OrderStatus
    total_amount: float
    currency: str = Field(default="USD")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[OrderItemSchema] = []

    class Config:
        from_attributes = True

class OrderFilterSchema(BaseModel):
    user_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 10
    offset: int = 0

class UpdateOrderSchema(BaseModel):
    status: Optional[OrderStatus] = None           # e.g. from Pending → Completed
    currency: Optional[str] = None                 # if allowed
    total_amount: Optional[float] = None           # only if it's a draft or editable order
    items: Optional[List[OrderItemSchema]] = None  # only if you're allowing item updates

    class Config:
        from_attributes = True