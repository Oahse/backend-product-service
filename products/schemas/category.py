from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy.dialects.postgresql import UUID
import uuid

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: UUID

    class Config:
        from_attributes = True