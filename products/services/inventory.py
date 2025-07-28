from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update, delete
from sqlalchemy import and_, or_
from typing import List, Optional
from models.products import (Product, Inventory, UUID, uuid)
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

    async def get_by_id(self, inventory_id: UUID) -> Inventory:
        result = await self.db.execute(select(Inventory).where(Inventory.id == inventory_id))
        inventory = result.scalar_one_or_none()
        return inventory


    async def create(self, inventory_in: InventoryCreate) -> Inventory:
        inventory = Inventory(
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


    async def update(self, inventory_id: UUID, inventory_in: InventoryCreate) -> Inventory:
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


    async def delete(self, inventory_id: UUID) -> bool:
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

