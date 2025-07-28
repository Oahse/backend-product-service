from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, update, delete
from typing import List, Optional
from core.utils.generator import generator
from datetime import datetime, timedelta
from models.promocode import (PromoCode, UUID, uuid)
from schemas.promocode import (PromoCodeCreate)


class PromoCodeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        active: Optional[bool] = None,
        valid_on: Optional[datetime] = None,
        code_contains: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Optional[List[PromoCode]]:
        try:
            query = select(PromoCode)
            filters = []

            if active is not None:
                filters.append(PromoCode.active == active)

            if valid_on:
                filters.append(PromoCode.valid_from <= valid_on)
                filters.append(PromoCode.valid_until >= valid_on)

            if code_contains:
                filters.append(PromoCode.code.ilike(f"%{code_contains}%"))

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)

            return result.scalars().all()

        except SQLAlchemyError as e:
            await self.db.rollback()
            return e
    
    async def get_by_id(self, promo_code_id: UUID) -> PromoCode:
        result = await self.db.execute(
            select(PromoCode).where(PromoCode.id == promo_code_id)
        )
        promo = result.scalar_one_or_none()
        return promo

    async def create(self, promo_in: PromoCodeCreate) -> PromoCode:
        promo = PromoCode(
            code=promo_in.code,
            discount_percent=promo_in.discount_percent,
            active=promo_in.active,
            valid_from=promo_in.valid_from,
            valid_until=promo_in.valid_until
        )

        try:
            self.db.add(promo)
            await self.db.commit()
            await self.db.refresh(promo)
            return promo
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise RuntimeError("Failed to create promo code.") from e

    async def update(self, promo_code_id: UUID, promo_in: PromoCodeCreate) -> PromoCode:
        promo = await self.get_by_id(promo_code_id)
        if not promo:
            raise None

        try:
            promo.code = promo_in.code
            promo.discount_percent = promo_in.discount_percent
            promo.active = promo_in.active
            promo.valid_from = promo_in.valid_from
            promo.valid_until = promo_in.valid_until

            await self.db.commit()
            await self.db.refresh(promo)
            return promo
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise RuntimeError("Failed to update promo code.") from e

    async def delete(self, promo_code_id: UUID) -> bool:
        promo = await self.get_by_id(promo_code_id)
        if not promo:
            raise None

        try:
            await self.db.delete(promo)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise RuntimeError("Failed to delete promo code.") from e

