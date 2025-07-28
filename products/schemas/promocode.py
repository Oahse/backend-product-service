from datetime import datetime

from pydantic import BaseModel, Field, condecimal
from sqlalchemy.dialects.postgresql import UUID
import uuid

class PromoCodeBase(BaseModel):
    code: str = Field(..., max_length=50)
    discount_percent: condecimal(max_digits=5, decimal_places=2)
    active: bool = True
    valid_from: datetime
    valid_until: datetime

class PromoCodeCreate(PromoCodeBase):
    pass

class PromoCodeRead(PromoCodeBase):
    id: UUID

    class Config:
        from_attributes = True
