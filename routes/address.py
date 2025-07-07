from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database import get_db
from core.utils.response import Response
from schemas.user import AddressCreate, AddressUpdate, AddressRead
from services.address import AddressService

router = APIRouter(prefix='/api/v1', tags=["Addresses"])

@router.post("/")
async def create_address(address_in: AddressCreate, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    try:
        address = await service.create_address(
            user_id=address_in.user_id,
            street=address_in.street,
            city=address_in.city,
            state=address_in.state,
            country=address_in.country,
            post_code=address_in.post_code,
            kind=address_in.kind,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(data=address, code=201)


@router.get("/{address_id}")
async def get_address(address_id: int, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    address = await service.get_address_by_id(address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return Response(data=address)


@router.put("/{address_id}")
async def update_address(address_id: int, address_in: AddressUpdate, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    updated_address = await service.update_address(address_id, **address_in.dict(exclude_unset=True))
    if not updated_address:
        raise HTTPException(status_code=404, detail="Address not found")
    return Response(data=updated_address)


@router.delete("/{address_id}")
async def delete_address(address_id: int, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    success = await service.delete_address(address_id)
    if not success:
        raise HTTPException(status_code=404, detail="Address not found or could not be deleted")
    return Response(data=True)


@router.get("/")
async def list_addresses(user_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = AddressService(db)
    addresses = await service.list_addresses(user_id=user_id, skip=skip, limit=limit)
    return Response(data=addresses)
