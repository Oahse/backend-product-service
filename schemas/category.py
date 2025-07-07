from typing import Optional

from pydantic import BaseModel, Field

class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: str

    class Config:
        from_attributes = True