from fastapi import APIRouter, Depends, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.inventory import InventoryService
from schemas.inventory import InventoryCreate
from core.utils.response import Response
from sqlalchemy.dialects.postgresql import UUID
import uuid

router = APIRouter(prefix="/api/v1/inventories", tags=["Inventories"])


@router.get("/")
async def get_all_inventories(
    name: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    svc = InventoryService(db)
    try:
        invs = await svc.get_all(name, location, limit, offset)
        return Response(data=[inv.to_dict() for inv in invs])
    except Exception as e:
        return Response(data=str(e), code=500)


@router.get("/{inventory_id}")
async def get_inventory(inventory_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = InventoryService(db)
    try:
        inv = await svc.get_by_id(inventory_id)
        if inv is None:
            return Response(message=f"Inventory with id '{inventory_id}' not found.", code=404)
        return Response(data=inv.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_inventory(inventory_in: InventoryCreate, db: AsyncSession = Depends(get_db)):
    svc = InventoryService(db)
    try:
        inv = await svc.create(inventory_in)
        return Response(data=inv.to_dict(), code=201)
    except Exception as e:
        return Response(data=str(e), code=500)


@router.put("/{inventory_id}")
async def update_inventory(inventory_id: UUID, inventory_in: InventoryCreate, db: AsyncSession = Depends(get_db)):
    svc = InventoryService(db)
    try:
        inv = await svc.update(inventory_id, inventory_in)
        if inv is None:
            return Response(message=f"Inventory with id '{inventory_id}' not found.", code=404)
        return Response(data=inv.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.delete("/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory(inventory_id: UUID, db: AsyncSession = Depends(get_db)):
    svc = InventoryService(db)
    try:
        res = await svc.delete(inventory_id)
        if not res:
            return Response(message=f"Inventory with id '{inventory_id}' not found.", code=404)
        return Response(message="Inventory deleted successfully", code=204)
    except Exception as e:
        return Response(data=str(e), code=500)

