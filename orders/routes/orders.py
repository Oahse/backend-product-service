from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from schemas.orders import OrderSchema, OrderItemSchema,UpdateOrderSchema,OrderFilterSchema
from models.orders import Order, OrderItem, OrderStatus
from services.orders import OrderService, OrderItemService
from core.database import get_db  # Make sure this returns AsyncSession
from core.utils.response import Response

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


# --- Order Routes --- #

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(order_in: OrderSchema,db: AsyncSession = Depends(get_db)):
    try:
        service = OrderService(db)
        order = await service.create_order(order_in)
        return Response(data=order.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        service = OrderService(db)
        order = await service.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return Response(data=order.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.put("/{order_id}")
async def update_order(order_id: str, update_data: UpdateOrderSchema, db: AsyncSession = Depends(get_db)):
    try:
        service = OrderService(db)
        order = await service.update_order(order_id, update_data)
        return Response(data=order.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        service = OrderService(db)
        deleted = await service.delete_order(order_id)
        if not deleted:
            return Response(success=False, message=f"Order with id '{order_id}' not found.", code=404)
        return Response(message="Order deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/")
async def get_all_orders(
    user_id: Optional[str] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = OrderService(db)
        orders = await service.get_all(
            user_id=user_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return Response(data=[order.to_dict() for order in orders])
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


# --- Order Item Routes --- #

@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_order_item(
    order_id: str,
    product_id: str,
    quantity: int,
    price_per_unit: float,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = OrderItemService(db)
        item = await service.create_order_item(order_id, product_id, quantity, price_per_unit)
        return Response(data=item.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/items/{item_id}")
async def get_order_item(item_id: str, db: AsyncSession = Depends(get_db)):
    try:
        service = OrderItemService(db)
        item = await service.get_order_item(item_id)
        return Response(data=item.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.put("/items/{item_id}")
async def update_order_item(item_id: str, update_data:OrderItemSchema, db: AsyncSession = Depends(get_db)):
    try:
        service = OrderItemService(db)
        item = await service.update_order_item(item_id, update_data)
        return Response(data=item.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_item(item_id: str, db: AsyncSession = Depends(get_db)):
    try:
        service = OrderItemService(db)
        deleted = await service.delete_order_item(item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Order item not found")
        return Response(message="Order item deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/{order_id}/items")
async def list_items_for_order(order_id: str,
            product_id: Optional[str] = None,
            quantity: Optional[int] = None,
            price_per_unit: Optional[float] = None,
            limit: int = 10,
            offset: int = 0, 
            db: AsyncSession = Depends(get_db)):
    try:
        service = OrderItemService(db)
        items = await service.get_all(order_id=order_id,product_id=product_id,quantity=quantity,price_per_unit=price_per_unit,limit=limit,offset=offset)
        return Response(data=[item.to_dict() for item in items])
    except Exception as e:
        return Response(success=False, message=str(e), code=500)

