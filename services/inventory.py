from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update, delete
from sqlalchemy import and_, or_
from typing import List, Optional
from core.utils.generator import generator
from models.inventory import (Product, Inventory,InventoryProduct)
from schemas.inventory import (InventoryCreate)
from core.utils.response import NotFoundError

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        name: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Inventory]:
        try:
            query = select(Inventory)
            filters = []

            if name:
                filters.append(Inventory.name.ilike(f"%{name}%"))
            if location:
                filters.append(Inventory.location.ilike(f"%{location}%"))

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            # optionally log error
            raise RuntimeError("Failed to fetch inventories") from e

    async def get_by_id(self, inventory_id: str) -> Inventory:
        result = await self.db.execute(select(Inventory).where(Inventory.id == inventory_id))
        inventory = result.scalar_one_or_none()
        if not inventory:
            raise None
        return inventory


    async def create(self, inventory_in: InventoryCreate) -> Inventory:
        inventory = Inventory(
            id=str(generator.get_id()),
            name=inventory_in.name,
            location=inventory_in.location
        )
        self.db.add(inventory)
        try:
            await self.db.commit()
            await self.db.refresh(inventory)
            return inventory
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e


    async def update(self, inventory_id: str, inventory_in: InventoryCreate) -> Inventory:
        inventory = await self.get_by_id(inventory_id)
        if not inventory:
            raise None
        
        inventory.name = inventory_in.name
        inventory.location = inventory_in.location

        try:
            await self.db.commit()
            await self.db.refresh(inventory)
            return inventory
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e


    async def delete(self, inventory_id: str) -> bool:
        inventory = await self.get_by_id(inventory_id)
        if not inventory:
            raise None
        
        try:
            await self.db.delete(inventory)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e



class InventoryProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        inventory_id: Optional[str] = None,
        product_id: Optional[str] = None,
        min_quantity: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[InventoryProduct]:
        try:
            query = select(InventoryProduct)
            filters = []

            if inventory_id:
                filters.append(InventoryProduct.inventory_id == inventory_id)
            if product_id:
                filters.append(InventoryProduct.product_id == product_id)
            if min_quantity is not None:
                filters.append(InventoryProduct.quantity >= min_quantity)

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            # Log the error here if you want
            # e.g. logger.error(f"Error fetching inventory products: {e}")
            await self.db.rollback()
            raise  e 

    async def get_by_id(self, entry_id: str) -> InventoryProduct:
        result = await self.db.execute(select(InventoryProduct).where(InventoryProduct.id == entry_id))
        entry = result.scalar_one_or_none()
        return entry

    async def create(
        self,
        inventory_id: str,
        product_id: str,
        quantity: int = 0,
        low_stock_threshold: int = 5
    ) -> tuple[Optional[InventoryProduct], Optional[Exception]]:
        # Check if inventory exists
        inventory = await self.db.execute(select(Inventory).where(Inventory.id == inventory_id))
        inventory_obj = inventory.scalar_one_or_none()
        if not inventory_obj:
            raise NotFoundError(f"Inventory with id {inventory_id} not found")

        # Check if product exists
        product = await self.db.execute(select(Product).where(Product.id == product_id))
        product_obj = product.scalar_one_or_none()
        if not product_obj:
            raise NotFoundError(f"Product with id {product_id} not found")

        entry = InventoryProduct(
            id=str(generator.get_id()),
            inventory_id=inventory_id,
            product_id=product_id,
            quantity=quantity,
            low_stock_threshold=low_stock_threshold
        )

        self.db.add(entry)
        try:
            await self.db.commit()
            await self.db.refresh(entry)
            return entry
        except Exception as e:
            await self.db.rollback()
            return e

    

    async def update(
        self,
        entry_id: str,
        quantity: Optional[int] = None,
        low_stock_threshold: Optional[int] = None
    ) -> tuple[bool, Optional[Exception]]:
        entry = await self.get_by_id(entry_id)
        if not entry:
            raise None

        if quantity is not None:
            entry.quantity = quantity
        if low_stock_threshold is not None:
            entry.low_stock_threshold = low_stock_threshold

        try:
            await self.db.commit()
            await self.db.refresh(entry)
            return entry
        except Exception as e:
            await self.db.rollback()
            return e

    async def delete(self, entry_id: str) -> bool:
        entry = await self.get_by_id(entry_id)
        
        if not entry:
            return None
        try:
            await self.db.delete(entry)
            await self.db.commit()
            return True
        except Exception as e:
            # Optionally log the exception here
            # e.g. logger.error(f"Failed to delete entry {entry_id}: {e}")
            await self.db.rollback()  # rollback on error
            raise e
