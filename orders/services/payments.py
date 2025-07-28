from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from uuid import UUID
from datetime import datetime
from models.payments import Payment, PaymentStatus, PaymentMethod  # adjust import as needed


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(
        self,
        order_id: str,
        method: PaymentMethod,
        amount: float,
        currency: str,
        user_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        gateway_response: Optional[str] = None,
        status: PaymentStatus = PaymentStatus.Pending,
        parent_payment_id: Optional[str] = None,
        refunded_amount: float = 0.0,
    ) -> Payment:
        try:
            payment_id = str(generator.get_id())
            payment = Payment(
                id=payment_id,
                order_id=order_id,
                method=method,
                amount=amount,
                currency=currency,
                user_id=user_id,
                transaction_id=transaction_id,
                gateway_response=gateway_response,
                status=status,
                parent_payment_id=parent_payment_id,
                refunded_amount=refunded_amount,
            )
            self.db.add(payment)
            await self.db.flush()  # flush to get ID if needed
            return payment
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    async def update_payment(
        self,
        payment_id: str,
        **kwargs
    ) -> Optional[Payment]:
        # Fetch existing payment
        payment = await self.get_payment(payment_id)
        if not payment:
            raise Exception("Payment not found")
        try:
            # Update attributes
            for key, value in kwargs.items():
                if hasattr(payment, key):
                    setattr(payment, key, value)

            await self.db.flush()
            return payment
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_payment(self, payment_id: str) -> bool:
        
        payment = await self.get_payment(payment_id)
        if not payment:
            raise Exception("Payment not found")
        try:
            await self.db.delete(payment)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_all(
        self,
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
    ) -> List[Payment]:
        try:
            query = select(Payment)
            filters = []

            if order_id:
                filters.append(Payment.order_id == order_id)
            if user_id:
                filters.append(Payment.user_id == user_id)
            if method:
                filters.append(Payment.method == method)
            if status:
                filters.append(Payment.status == status)
            if amount is not None:
                filters.append(Payment.amount == amount)
            if currency:
                filters.append(Payment.currency == currency)
            if transaction_id:
                filters.append(Payment.transaction_id == transaction_id)
            if gateway_response:
                filters.append(Payment.gateway_response == gateway_response)
            if created_at:
                filters.append(Payment.created_at == created_at)
            if updated_at:
                filters.append(Payment.updated_at == updated_at)
            if refunded_amount is not None:
                filters.append(Payment.refunded_amount == refunded_amount)
            if parent_payment_id:
                filters.append(Payment.parent_payment_id == parent_payment_id)

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            payments = result.scalars().all()

            return payments

        except Exception as e:
            await self.db.rollback()
            raise e