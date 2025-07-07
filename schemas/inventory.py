from typing import Optional
from pydantic import BaseModel 
# ---------- Inventory Schemas ----------

class InventoryBase(BaseModel):
    name: str
    location: Optional[str] = None


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(InventoryBase):
    pass


class InventoryRead(InventoryBase):
    id: str

    class Config:
        from_attributes = True


# ---------- InventoryProduct Schemas ----------

class InventoryProductBase(BaseModel):
    quantity: int = 0
    low_stock_threshold: int = 5


class InventoryProductCreate(InventoryProductBase):
    inventory_id: str
    product_id: str


class InventoryProductUpdate(InventoryProductBase):
    pass


class InventoryProductRead(InventoryProductBase):
    id: str
    inventory_id: str
    product_id: str

    class Config:
        from_attributes = True