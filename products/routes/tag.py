from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from services.tag import TagService
from schemas.tag import TagCreate
from core.utils.response import Response
from sqlalchemy.dialects.postgresql import UUID
import uuid
router = APIRouter(prefix="/api/v1/tags", tags=["Tags"])


@router.get("/")
async def get_all_tags(
    name: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    service = TagService(db)
    try:
        tags = await service.get_all(name=name, limit=limit, offset=offset)
        return Response(data=[tag.to_dict() for tag in tags])
    except Exception as e:
        return Response(data=str(e), code=500)


@router.get("/{tag_id}")
async def get_tag_by_id(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    try:
        tag = await service.get_by_id(tag_id)
        if tag is None:
            return Response(message=f"Tag with id '{tag_id}' not found.",code=404)
        return Response(data=tag.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tag(tag_in: TagCreate, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    try:
        tag = await service.create(tag_in)
        return Response(data=tag.to_dict(), code=201)
    except Exception as e:
        return Response(data=str(e), code=500)


@router.put("/{tag_id}")
async def update_tag(tag_id: UUID, tag_in: TagCreate, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    try:
        tag = await service.update(tag_id, tag_in)
        if tag  is None:
            return Response(message=f"Tag with id '{tag_id}' not found.",code=404)
        return Response(data=tag.to_dict())
    
    except Exception as e:
        return Response(data=str(e), code=500)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    service = TagService(db)
    try:
        tag = await service.delete(tag_id)
        if tag  is None:
            return Response(message=f"Tag with id '{tag_id}' not found.",code=404)
        return Response(message="Tag deleted successfully", code=204)
    except Exception as e:
        return Response(data=str(e), code=500)
