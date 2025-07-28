from typing import Optional
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID
import uuid
# ---------- Inventory Schemas ----------

class InventoryBase(BaseModel):
    name: str
    location: Optional[str] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(InventoryBase):
    pass

class InventoryRead(InventoryBase):
    id: UUID

    class Config:
        from_attributes = True
