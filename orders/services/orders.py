from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update, delete,and_
from uuid import UUID
from core.utils.generator import generator
from models.orders import Order, OrderItem, OrderStatus  # adjust import
from schemas.orders import OrderSchema, OrderItemSchema,UpdateOrderSchema,OrderFilterSchema
from core.config import settings
from core.utils.kafka import KafkaProducer, send_kafka_message, is_kafka_available
from datetime import datetime

kafka_producer = KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS,
                                topic=str(settings.KAFKA_TOPIC))

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self,order_in: OrderSchema) -> Order:
        try:
            order_id = str(generator.get_id())
            order = Order(id = order_id, 
                user_id=order_in.user_id, 
                total_amount=order_in.total_amount, 
                currency=order_in.currency,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(), 
                status=order_in.status
            )
            self.db.add(order)
            await self.db.flush()  # flush to get order.id

            if order_in.items:
                for item_data in order_in.items:
                    item = OrderItem(
                        id = str(generator.get_id()),
                        order_id=order_id,
                        product_id=item_data.product_id,
                        quantity=item_data.quantity,
                        price_per_unit=item_data.price_per_unit,
                        total_price = item_data.total_price if item_data.total_price is not None else item_data.quantity * item_data.price_per_unit
                    )
                    self.db.add(item)

            await self.db.commit()

            
            # Reload product with relationships eagerly loaded
            order = await self.get_order_by_id(order_id)
            
            # Kafka background task
            await kafka_producer.start()
            await kafka_producer.send({
                    "order": order.to_dict(),
                    "action": "create"
                })
            await kafka_producer.stop()
            await self.db.refresh(order)
            return order
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        result = await self.db.execute(select(Order)
                    .options(
                        selectinload(Order.items)
                    ).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def update_order(self, order_id: str, update_data: UpdateOrderSchema) -> Optional[Order]:
        order = await self.get_order_by_id(order_id)
        if not order:
            raise Exception("Order not found")

        try:
            data = update_data.model_dump(exclude_unset=True)

            # Update allowed fields
            if "status" in data:
                order.status = data["status"]
            if "total_amount" in data:
                order.total_amount = data["total_amount"]
            if "currency" in data:
                order.currency = data["currency"]
            order.updated_at = data.get("updated_at", datetime.utcnow())

            # Handle items
            if "items" in data and data["items"] is not None:
                # Delete existing items
                await self.db.execute(
                    delete(OrderItem).where(OrderItem.order_id == order.id)
                )

                # Add new items
                for item_data in data["items"]:
                    
                    new_item = OrderItem(
                        id=str(generator.get_id()),
                        order_id=order.id,
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        price_per_unit=item_data['price_per_unit'],
                        total_price=(
                            item_data['total_price']
                            if item_data['total_price'] is not None
                            else item_data['quantity'] * item_data['price_per_unit']
                        )
                    )
                    self.db.add(new_item)  # ✅ Move this inside the loop

            await self.db.flush()
            await self.db.refresh(order)
            await self.db.commit()
            return order

        except Exception as e:
            await self.db.rollback()
            raise e


    async def delete_order(self, order_id: str) -> bool:
        order = await self.get_order_by_id(order_id)
        if not order:
            raise Exception("Order not found")
        try:
            await self.db.delete(order)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_all(
        self,
        user_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Order]:
        try:
            query = select(Order).options(
                selectinload(Order.items)
            )

            if user_id:
                query = query.where(Order.user_id == user_id)
            if status:
                query = query.where(Order.status == status)
            if start_date:
                query = query.where(Order.created_at >= start_date)
            if end_date:
                query = query.where(Order.created_at <= end_date)

            query = query.offset(offset).limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            await self.db.rollback()
            raise e


class OrderItemService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order_item(
        self,
        order_id: str,
        product_id: str,
        quantity: int,
        price_per_unit: float,
    ) -> OrderItem:
        try:
            total_price = quantity * price_per_unit
            item = OrderItem(
                id = str(generator.get_id()),
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                price_per_unit=price_per_unit,
                total_price=total_price,
            )
            self.db.add(item)
            await self.db.flush()
            await self.db.commit() 
            return item
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_order_item(self, item_id: str) -> Optional[OrderItem]:
        result = await self.db.execute(select(OrderItem).where(OrderItem.id == item_id))
        return result.scalar_one_or_none()

    async def update_order_item(self, item_id: str, update_data:OrderItemSchema) -> Optional[OrderItem]:
        item = await self.get_order_item(item_id)
        if not item:
            raise Exception("OrderItem not found")

        try:
            data = update_data.model_dump(exclude_unset=True)

            # Update allowed fields
            if "product_id" in data:
                item.product_id = data["product_id"]
            if "quantity" in data:
                item.quantity = data["quantity"]
            if "price_per_unit" in data:
                item.price_per_unit = data["price_per_unit"]
            if "total_price" in data:
                item.total_price = data["total_price"]
            

            # Recalculate total_price if quantity or price_per_unit changed and total_price not explicitly set
            if ("quantity" in kwargs or "price_per_unit" in kwargs) and "total_price" not in kwargs:
                item.total_price = item.quantity * item.price_per_unit

            await self.db.flush()
            await self.db.refresh(item)
            await self.db.commit()  # ✅ Ensure the update is persisted

            return item

        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_order_item(self, item_id: str) -> bool:
        item = await self.get_order_item(item_id)
        if not item:
            raise Exception("OrderItem not found")
        try:
            await self.db.delete(item)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e


    async def get_all(
            self,
            order_id: Optional[str] = None,
            product_id: Optional[str] = None,
            quantity: Optional[int] = None,
            price_per_unit: Optional[float] = None,
            limit: int = 10,
            offset: int = 0,
        ) -> List[OrderItem]:
        try:
            query = select(OrderItem).options(
                selectinload(OrderItem.order)  # eager load related Order if needed
            )

            filters = []

            if order_id:
                filters.append(OrderItem.order_id == order_id)
            if product_id:
                filters.append(OrderItem.product_id == product_id)
            if quantity is not None:
                filters.append(OrderItem.quantity == quantity)
            if price_per_unit is not None:
                filters.append(OrderItem.price_per_unit == price_per_unit)

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)

            result = await self.db.execute(query)
            items = result.scalars().all()

            return items

        except Exception as e:
            await self.db.rollback()
            raise e
