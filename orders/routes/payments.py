from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from models.payments import Payment, PaymentMethod, PaymentStatus  # adjust imports
from services.payments import PaymentService  # async service for payments
from core.database import get_db  # async session dependency
from core.utils.response import Response
from datetime import datetime

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_payment(
    order_id: str,
    amount: float,
    currency: str,
    method: PaymentMethod,
    user_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    gateway_response: Optional[str] = None,
    parent_payment_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = PaymentService(db)
        payment = await service.create_payment(
            order_id=order_id,
            amount=amount,
            currency=currency,
            method=method,
            user_id=user_id,
            transaction_id=transaction_id,
            gateway_response=gateway_response,
            parent_payment_id=parent_payment_id,
        )
        
        return Response(data=payment.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)

@router.get("/{payment_id}")
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    try:
        service = PaymentService(db)
        payment = await service.get_payment(payment_id)
        return Response(data=payment.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.put("/{payment_id}")
async def update_payment(payment_id: str, update_data: dict, db: AsyncSession = Depends(get_db)):
    try:
        service = PaymentService(db)
        payment = await service.update_payment(payment_id, **update_data)
        return Response(data=payment.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    try:
        service = PaymentService(db)
        deleted = await service.delete_payment(payment_id)
        if not deleted:
            return Response(success=False, message=f"Payment with id '{payment_id}' not found.", code=404)
        return Response(message="Payment deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/")
async def get_all_payments(
        order_id: Optional[str] = None,
        user_id: Optional[str] = None,
        method: Optional[PaymentMethod] = None,
        status: Optional[PaymentStatus] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
        transaction_id: Optional[str] = None,
        gateway_response: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        refunded_amount: Optional[float] = None,
        parent_payment_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0, 
        db: AsyncSession = Depends(get_db)):
    try:
        service = PaymentService(db)
        payments = await service.get_all(order_id)
        return Response(data=[payment.to_dict() for payment in payments])
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


