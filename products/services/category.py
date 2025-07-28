from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_

from typing import List, Optional
from models.category import (Category, UUID, uuid)
from schemas.category import (CategoryCreate)
from core.utils.response import NotFoundError

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        name: Optional[str] = None,
        description_contains: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Category]:
        query = select(Category)
        filters = []

        if name:
            filters.append(Category.name.ilike(f"%{name}%"))
        if description_contains:
            filters.append(Category.description.ilike(f"%{description_contains}%"))

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)

        try:
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e

    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        return category


    async def create(self, category_in: CategoryCreate) -> Category:
        category = Category(
            name=category_in.name,
            description=category_in.description,
        )
        self.db.add(category)
        try:
            await self.db.commit()
            await self.db.refresh(category)
            return category
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e

    async def update(self, category_id: UUID, category_in: CategoryCreate) -> Category:
        category = await self.get_by_id(category_id)
        if not category:
            return None
        try:
            category.name = category_in.name
            category.description = category_in.description
            await self.db.commit()
            await self.db.refresh(category)
            return category
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e

    async def delete(self, category_id: UUID) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            return None
        try:
            await self.db.delete(category)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e

