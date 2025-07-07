from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy import and_, or_
from fastapi import APIRouter, Depends, status, BackgroundTasks
from typing import List, Optional
from core.utils.generator import generator
from datetime import datetime, timedelta
from core.database import AsyncElasticsearch
from models.products import (Product, ProductVariant, ProductImage,AvailabilityStatus)
from schemas.products import (ProductCreate,ProductVariantCreate,ProductVariantUpdate)
from models.tag import (Tag)
from models.inventory import(InventoryProduct)
from core.config import settings
from core.utils.kafka import KafkaProducer , send_kafka_message
background_tasks= BackgroundTasks
class ProductService:
    def __init__(self, db: AsyncSession, es: AsyncElasticsearch):  
        self.db = db
        self.es = es
    async def search(
        self,
        q: Optional[str] = None,
        name: Optional[str] = None,
        sku: Optional[str] = None,
        category_id: Optional[str] = None,
        tag_id: Optional[str] = None,
        availability: Optional[AvailabilityStatus] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List:
        try:
            must_clauses = []

            # Full-text search on name and description
            if q:
                must_clauses.append({
                    "multi_match": {
                        "query": q,
                        "fields": ["name", "description"]
                    }
                })

            # Exact match fields
            if name:
                must_clauses.append({"match": {"name": name}})
            if sku:
                must_clauses.append({"match": {"sku": sku}})
            if category_id:
                must_clauses.append({"term": {"category_id": category_id}})
            if tag_id:
                must_clauses.append({"term": {"tag_ids": tag_id}})
            if availability:
                must_clauses.append({"term": {"availability": availability.value}})
            if min_price is not None or max_price is not None:
                range_query = {}
                if min_price is not None:
                    range_query["gte"] = min_price
                if max_price is not None:
                    range_query["lte"] = max_price
                must_clauses.append({"range": {"price": range_query}})
            if min_rating is not None:
                must_clauses.append({"range": {"rating": {"gte": min_rating}}})

            query_body = {
                "query": {
                    "bool": {
                        "must": must_clauses or [{"match_all": {}}]
                    }
                },
                "from": offset,
                "size": limit
            }

            result = await self.es.search(index="products", body=query_body)
            return [hit["_source"] for hit in result["hits"]["hits"]]
        except Exception as e:
            raise e  # or raise a custom error wrapping `e`
    
    async def get_all(
        self,
        name: Optional[str] = None,
        sku: Optional[str] = None,
        category_id: Optional[str] = None,
        tag_id: Optional[str] = None,
        availability: Optional[AvailabilityStatus] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Product]:
        try:
            query = select(Product)

            filters = []
            if name:
                filters.append(Product.name.ilike(f"%{name}%"))
            if sku:
                filters.append(Product.sku == sku)
            if category_id:
                filters.append(Product.category_id == category_id)
            if availability:
                filters.append(Product.availability == availability)
            if min_price is not None:
                filters.append(Product.base_price >= min_price)
            if max_price is not None:
                filters.append(Product.base_price <= max_price)
            if min_rating is not None:
                filters.append(Product.rating >= min_rating)

            if tag_id:
                query = query.join(Product.tags)
                filters.append(Tag.id == tag_id)
                query = query.distinct()  # prevent duplicates from join

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)

            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            # Optionally log the error here
            await self.db.rollback()
            raise e  # or raise a custom error wrapping `e`
    
    async def get_by_id(self, product_id: int) -> Product:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        return product


    async def create(self, product_in: ProductCreate) -> Product:
        try:
            tags = []
            if product_in.tag_ids:
                result = await self.db.execute(select(Tag).where(Tag.id.in_(product_in.tag_ids)))
                tags = result.scalars().all()

            product = Product(
                id=str(generator.get_id()),
                name=product_in.name,
                sku=product_in.sku,
                description=product_in.description,
                base_price=product_in.base_price,
                sale_price=product_in.sale_price,
                availability=product_in.availability,
                rating=product_in.rating or 0.0,
                category_id=product_in.category_id,
                tags=tags
            )
            self.db.add(product)
            await self.db.flush()

            for variant_in in product_in.variants or []:
                variant = ProductVariant(
                    product_id=product.id,
                    variant_name=variant_in.variant_name,
                    sku=variant_in.sku,
                    price=variant_in.price,
                    stock=variant_in.stock,
                )
                self.db.add(variant)

            for image_in in product_in.images or []:
                image = ProductImage(
                    product_id=product.id,
                    url=image_in.url,
                    alt_text=image_in.alt_text,
                    is_primary=image_in.is_primary,
                )
                self.db.add(image)

            if product_in.inventory:
                for entry in product_in.inventory:
                    inventory_product = InventoryProduct(
                        id=str(generator.get_id()),
                        inventory_id=entry.inventory_id,
                        product_id=product.id,
                        quantity=entry.quantity,
                        low_stock_threshold=entry.low_stock_threshold,
                    )
                    self.db.add(inventory_product)

            await self.db.commit()
            await self.db.refresh(product)
            # Add Kafka sending as background task
            result =product
            background_tasks.add_task(
                send_kafka_message,
                KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS, 
                              topic=str(settings.KAFKA_TOPIC)
                              ),

                {
                    "product": result.to_dict(),
                    'es':self.es,
                    "action": "create"
                }
            )
            return result

        except Exception as e:
            await self.db.rollback()
            # Optionally log error here
            raise e


    async def update(self, product_id: int, product_in: ProductCreate) -> Product:
        product = await self.get_by_id(product_id)
        if not product:
            raise None

        try:
            if product_in.name is not None:
                product.name = product_in.name
            if product_in.sku is not None:
                product.sku = product_in.sku
            if product_in.description is not None:
                product.description = product_in.description
            if product_in.base_price is not None:
                product.base_price = product_in.base_price
            if product_in.sale_price is not None:
                product.sale_price = product_in.sale_price
            if product_in.availability is not None:
                product.availability = product_in.availability
            if product_in.rating is not None:
                product.rating = product_in.rating
            if product_in.category_id is not None:
                product.category_id = product_in.category_id

            if product_in.tag_ids is not None:
                result = await self.db.execute(select(Tag).where(Tag.id.in_(product_in.tag_ids)))
                product.tags = result.scalars().all()

            incoming_variant_ids = {v.id for v in (product_in.variants or []) if getattr(v, "id", None)}
            existing_variants = {v.id: v for v in product.variants}

            for variant_id in list(existing_variants.keys()):
                if variant_id not in incoming_variant_ids:
                    await self.db.delete(existing_variants[variant_id])

            for variant_in in product_in.variants or []:
                if variant_in.id in existing_variants:
                    variant = existing_variants[variant_in.id]
                    variant.variant_name = variant_in.variant_name
                    variant.sku = variant_in.sku
                    variant.price = variant_in.price
                    variant.stock = variant_in.stock
                else:
                    variant = ProductVariant(
                        product_id=product.id,
                        variant_name=variant_in.variant_name,
                        sku=variant_in.sku,
                        price=variant_in.price,
                        stock=variant_in.stock,
                    )
                    self.db.add(variant)

            incoming_image_ids = {i.id for i in (product_in.images or []) if getattr(i, "id", None)}
            existing_images = {i.id: i for i in product.images}

            for image_id in list(existing_images.keys()):
                if image_id not in incoming_image_ids:
                    await self.db.delete(existing_images[image_id])

            for image_in in product_in.images or []:
                if image_in.id in existing_images:
                    image = existing_images[image_in.id]
                    image.url = image_in.url
                    image.alt_text = image_in.alt_text
                    image.is_primary = image_in.is_primary
                else:
                    image = ProductImage(
                        product_id=product.id,
                        url=image_in.url,
                        alt_text=image_in.alt_text,
                        is_primary=image_in.is_primary,
                    )
                    self.db.add(image)

            # Remove existing inventory links
            await self.db.execute(
                delete(InventoryProduct).where(InventoryProduct.product_id == product.id)
            )

            # Add updated inventory entries
            if product_in.inventory:
                for entry in product_in.inventory:
                    inventory_product = InventoryProduct(
                        id=str(generator.get_id()),
                        inventory_id=entry.inventory_id,
                        product_id=product.id,
                        quantity=entry.quantity,
                        low_stock_threshold=entry.low_stock_threshold,
                    )
                    self.db.add(inventory_product)

            product.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(product)
            return product

        except Exception as e:
            await self.db.rollback()
            # Optionally log error here
            raise e


    async def delete(self, product_id: int) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            raise None
        try:
            await self.db.delete(product)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e


class ProductVariantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_variant(self, product_id: int, variant_in: ProductVariantCreate) -> ProductVariant:
        # Optionally check if product exists before adding variant
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise None
        
        variant = ProductVariant(
            product_id=product_id,
            variant_name=variant_in.variant_name,
            sku=variant_in.sku,
            price=variant_in.price,
            stock=variant_in.stock,
        )
        try:
            self.db.add(variant)
            await self.db.commit()
            await self.db.refresh(variant)
            return variant
        except Exception as e:
            await self.db.rollback()
            # Optionally log error here
            raise e


    async def get_by_id(self, variant_id: int) -> Optional[ProductVariant]:
        try:
            result = await self.db.execute(select(ProductVariant).where(ProductVariant.id == variant_id))
            variant = result.scalar_one_or_none()
            if not variant:
                raise None
            return variant
        except Exception as e:
            # Optionally log the exception here
            raise e


    async def get_all(
        self,
        product_id: Optional[str] = None,
        sku: Optional[str] = None,
        variant_name: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_stock: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[ProductVariant]:
        query = select(ProductVariant)
        filters = []

        if product_id:
            filters.append(ProductVariant.product_id == product_id)
        if sku:
            filters.append(ProductVariant.sku == sku)
        if variant_name:
            filters.append(ProductVariant.variant_name.ilike(f"%{variant_name}%"))
        if min_price is not None:
            filters.append(ProductVariant.price >= min_price)
        if max_price is not None:
            filters.append(ProductVariant.price <= max_price)
        if min_stock is not None:
            filters.append(ProductVariant.stock >= min_stock)

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)

        try:
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            # Optionally log the exception here
            raise e


    async def update(self, variant_id: int, variant_in: ProductVariantUpdate) -> ProductVariant:
        variant = await self.get_by_id(variant_id)
        if not variant:
            raise None
        
        for field, value in variant_in.dict(exclude_unset=True).items():
            setattr(variant, field, value)
        
        try:
            await self.db.commit()
            await self.db.refresh(variant)
            return variant
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e


    async def delete(self, variant_id: int) -> bool:
        variant = await self.get_by_id(variant_id)
        if not variant:
            raise None

        try:
            await self.db.delete(variant)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            # Optionally log the error here
            raise e


# 🛍️