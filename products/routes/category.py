from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database import get_db
from services.category import CategoryService
from schemas.category import CategoryCreate, CategoryRead
from core.utils.response import NotFoundError, Response
from sqlalchemy.dialects.postgresql import UUID
import uuid

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])

@router.get("/")
async def get_all_categories(
    name: Optional[str] = None,
    description_contains: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    service = CategoryService(db)
    try:
        res = await service.get_all(name, description_contains, limit, offset)
        return Response(data=[c.to_dict() for c in res])
    except Exception as e:
        return Response(data=str(e), code=500)


@router.get("/{category_id}")
async def get_category_by_id(category_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    try:
        res = await service.get_by_id(category_id)
        if res  is None:
            return Response(message=f"Category with id '{category_id}' not found.",code=404)
        return Response(data=res.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.post("/")
async def create_category(category_in: CategoryCreate, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    try:
        res = await service.create(category_in)
        return Response(data=res.to_dict(), code=201)
    except Exception as e:
        return Response(data=str(e), code=500)


@router.put("/{category_id}")
async def update_category(category_id: UUID, category_in: CategoryCreate, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    try:
        res = await service.update(category_id, category_in)
        if res is None:
            return Response(message=f"Category with id '{category_id}' not found.",code=404)
        return Response(data=res.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: UUID, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)
    try:
        res = await service.delete(category_id)
        if res is None:
            return Response(message=f"Category with id '{category_id}' not found.",code=404)
        return Response(message='Category deleted Successfully', code=204)
    except Exception as e:
        return Response(data=str(e), code=500)