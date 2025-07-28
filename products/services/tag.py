
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from models.tag import (Tag, uuid, UUID)
from schemas.tag import (TagCreate)
from core.utils.response import NotFoundError

class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        name: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Tag]:
        query = select(Tag)

        if name:
            query = query.where(Tag.name.ilike(f"%{name}%"))

        query = query.limit(limit).offset(offset)

        try:
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            # Optionally log the error here
            raise e

    async def get_by_id(self, tag_id: UUID) -> Tag:
        try:
            result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
            tag = result.scalar_one_or_none()
            return tag
        except Exception as e:
            # Optionally log the error here
            raise e

    async def create(self, tag_in: TagCreate) -> Tag:
        tag = Tag(name=tag_in.name)
        self.db.add(tag)
        try:
            await self.db.commit()
            await self.db.refresh(tag)
            return tag
        except Exception as e:
            await self.db.rollback()
            # Optionally log the exception here
            raise e

    async def update(self, tag_id: UUID, tag_in: TagCreate) -> Tag:
        tag = await self.get_by_id(tag_id)
        if not tag:
            raise None
        try:
            tag.name = tag_in.name
            await self.db.commit()
            await self.db.refresh(tag)
            return tag
        except Exception as e:
            await self.db.rollback()
            # Optional: log the exception here
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
            # Optional: log the error here
            raise e
