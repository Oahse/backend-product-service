from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from core.database import get_db
from services.promocode import PromoCodeService
from schemas.promocode import PromoCodeCreate
from core.utils.response import Response
from sqlalchemy.dialects.postgresql import UUID
import uuid
router = APIRouter(prefix="/api/v1/promocodes", tags=["Promo Codes"])


@router.get("/")
async def get_all_promocodes(
    active: Optional[bool] = None,
    valid_on: Optional[datetime] = None,
    code_contains: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    service = PromoCodeService(db)
    try:
        res = await service.get_all(active, valid_on, code_contains, limit, offset)
        return Response(data=[p.to_dict() for p in res])
    except Exception as e:
        return Response(data=str(e), code=500)


@router.get("/{promo_code_id}")
async def get_promocode_by_id(promo_code_id: UUID, db: AsyncSession = Depends(get_db)):
    service = PromoCodeService(db)
    try:
        res = await service.get_by_id(promo_code_id)
        if res is None:
            return Response(message=f"Promo code with id '{promo_code_id}' not found.", code=404)
        return Response(data=res.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_promocode(promo_in: PromoCodeCreate, db: AsyncSession = Depends(get_db)):
    service = PromoCodeService(db)
    try:
        res = await service.create(promo_in)
        return Response(data=res.to_dict(), code=201)
    except Exception as e:
        return Response(data=str(e), code=500)


@router.put("/{promo_code_id}")
async def update_promocode(promo_code_id: UUID, promo_in: PromoCodeCreate, db: AsyncSession = Depends(get_db)):
    service = PromoCodeService(db)
    try:
        res = await service.update(promo_code_id, promo_in)
        if res is None:
            return Response(message=f"Promo code with id '{promo_code_id}' not found.", code=404)
        return Response(data=res.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.delete("/{promo_code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promocode(promo_code_id: UUID, db: AsyncSession = Depends(get_db)):
    service = PromoCodeService(db)
    try:
        res = await service.delete(promo_code_id)
        if res is None:
            return Response(message=f"Promo code with id '{promo_code_id}' not found.", code=404)
        return Response(message="Promo code deleted successfully", code=204)
    except Exception as e:
        return Response(data=str(e), code=500)
