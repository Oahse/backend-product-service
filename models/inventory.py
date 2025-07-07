from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy import Integer, String, ForeignKey
from core.database import Base, CHAR_LENGTH
from typing import List, Optional
from models.products import Product

class InventoryProduct(Base):
    __tablename__ = "inventory_products"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    inventory_id: Mapped[str] = mapped_column(ForeignKey("inventories.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)

    quantity: Mapped[int] = mapped_column(Integer, default=0, index=True)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, index=True)

    product: Mapped["Product"] = relationship("Product", backref="inventory_entries")
    inventory: Mapped["Inventory"] = relationship("Inventory", backref="product_entries")


class Inventory(Base):
    __tablename__ = "inventories"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), index=False)
