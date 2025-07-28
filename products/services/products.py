from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import BackgroundTasks
from typing import List, Optional
from datetime import datetime
from sqlalchemy.exc import DBAPIError
from core.utils.generator import generator
from core.database import get_elastic_db
import json
from models.products import Product, ProductVariant, ProductVariantImage,ProductVariantAttribute, AvailabilityStatus, Tag,InventoryProduct
from schemas.products import ProductCreate, ProductVariantCreate,ProductVariantUpdate,ProductVariantRead,ProductVariantAttributeCreate, ProductVariantImageCreate
from services.category import CategoryService
from core.config import settings
from core.utils.kafka import KafkaProducer, send_kafka_message, is_kafka_available
from core.utils.barcode import Barcode
kafka_producer = KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS,
                                topic=str(settings.KAFKA_TOPIC))

def generate_barcode(data, logo_path=None, filename='barcode.png', save_as_png=False):
    barcode = Barcode()
    return barcode.generate_barcode(data=data, logo_path=logo_path, filename=filename, save_as_png=save_as_png)

def generate_sku(product_name: str, variant_name: str, unique_id: str) -> str:
    # Take first 3 letters of product name (uppercase, remove spaces)
    product_code = ''.join(product_name.upper().split())[:3]

    # Take first 3 letters of variant name (uppercase, remove spaces)
    variant_code = ''.join(variant_name.upper().split())[:3]

    # Use last 4 chars of unique_id or some unique suffix (can be timestamp, uuid, etc.)
    suffix = unique_id[-4:].upper()

    sku = f"{product_code}-{variant_code}-{suffix}"
    return sku


class ProductService:
    def __init__(self, db: AsyncSession, es):
        self.db = db
        self.es = es
    async def resolve_tags(self, tag_ids: List[str]) -> List[Tag]:
        if not tag_ids:
            return []
        result = await self.db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        return result.scalars().all()

    async def search(
        self,
        q: Optional[str] = None,
        name: Optional[str] = None,
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

            if q:
                must_clauses.append({
                    "multi_match": {
                        "query": q,
                        "fields": ["name", "description"]
                    }
                })

            if name:
                must_clauses.append({"match": {"name": name}})
            
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
                must_clauses.append({"range": {"base_price": range_query}})
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

            result = await self.es.search(index="products", query=query_body["query"], from_=offset, size=limit)

            return [hit["_source"] for hit in result["hits"]["hits"]]
        except Exception as e:
            raise e

    async def get_all(
        self,
        name: Optional[str] = None,
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
            query = select(Product).options(
                        selectinload(Product.category),
                        selectinload(Product.tags),
                        selectinload(Product.variants),
                        selectinload(Product.inventories),
                    )
            filters = []

            if name:
                filters.append(Product.name.ilike(f"%{name}%"))
            
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
                query = query.distinct()

            if filters:
                query = query.where(and_(*filters))

            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_by_id(self, product_id: str) -> Optional[Product]:
        result = await self.db.execute(select(Product).options(
                        selectinload(Product.category),
                        selectinload(Product.tags),
                        selectinload(Product.variants).selectinload(ProductVariant.images),
                        selectinload(Product.variants).selectinload(ProductVariant.attributes),

                        selectinload(Product.inventories),
                    ).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def create(self, product_in: ProductCreate) -> Product:
        tags = []
        if product_in.tag_ids:
            try:
                tags = await self.resolve_tags(product_in.tag_ids)
            except Exception as e:
                await self.db.rollback()
                # Optionally log the error here
                raise e
        category = CategoryService(self.db)

        res = await category.get_by_id(product_in.category_id)
        if res is None:
            raise ValueError(f"Invalid category_id: Category with {product_in.category_id} does not exist.")
        product_id = str(generator.get_id())
        product = Product(
            id=product_id,
            name=product_in.name,
            description=product_in.description,
            base_price=product_in.base_price,
            sale_price=product_in.sale_price,
            availability=AvailabilityStatus(product_in.availability),
            rating=product_in.rating or 0.0,
            category_id=product_in.category_id,
            tags=tags
        )
        self.db.add(product)
        try:
            
            await self.db.flush()
            for variant_in in product_in.variants or []:
                vid = str(generator.get_id())
                sku=generate_sku(product_in.name, variant_in.variant_name, vid)
                variant = ProductVariant(
                    id=vid,
                    product_id=product_id,
                    sku=sku,
                    price=variant_in.price,
                    stock=variant_in.stock,
                    barcode=str(generate_barcode(json.dumps({
                        'id':vid,
                        'product_id':product_id,
                        'sku':sku,
                        'price':variant_in.price,
                        'stock':variant_in.stock
                        }), 
                        logo_path=None, 
                        filename=f'{vid}.png', 
                        save_as_png=False)
                    )
                )
                self.db.add(variant)

            # Handle inventory ids (list) if provided
            if product_in.inventory_ids:
                for inv_id in product_in.inventory_ids:
                    inventory_product = InventoryProduct(
                        id=str(generator.get_id()),
                        inventory_id=inv_id,
                        product_id=product.id,
                        quantity=0,  # default quantity, adjust if you have quantity info
                        low_stock_threshold=0  # adjust if needed
                    )
                    self.db.add(inventory_product)
            await self.db.commit()

            
            # Reload product with relationships eagerly loaded
            product = await self.get_by_id(product_id)
            if not product:
                raise Exception("Product not found")
            # Kafka background task
            await kafka_producer.start()
            await kafka_producer.send({
                    "product": product.to_dict(),
                    "action": "create"
                })
            await kafka_producer.stop()
            # background_tasks.add_task(
            #     send_kafka_message,
            #     KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS,
            #                     topic=str(settings.KAFKA_TOPIC)),
            #     {
            #         "product": product.to_dict(),
            #         "es": self.es,
            #         "action": "create"
            #     }
            # )
            return product
        
        except Exception as e:
            print(e,'------','error')
            await self.db.rollback()
            raise e

    async def update(self, product_id: str, product_in: ProductCreate) -> Product:
        product = await self.get_by_id(product_id)
        if not product:
            raise Exception("Product not found")

        try:
            for field in ["name", "description", "base_price", "sale_price", "availability", "rating", "category_id"]:
                val = getattr(product_in, field, None)
                if val is not None:
                    setattr(product, field, val)

            if product_in.tag_ids is not None:
                product.tags = await self.resolve_tags(product_in.tag_ids)

            # Variants update logic
            incoming_variant_ids = {v.id for v in (product_in.variants or []) if getattr(v, "id", None)}
            existing_variants = {v.id: v for v in product.variants}

            for variant_id in list(existing_variants.keys()):
                if variant_id not in incoming_variant_ids:
                    await self.db.delete(existing_variants[variant_id])

            for variant_in in product_in.variants or []:
                if getattr(variant_in, "id", None) in existing_variants:
                    variant = existing_variants[variant_in.id]
                    variant.variant_name = variant_in.variant_name
                    variant.sku = variant_in.sku
                    variant.price = variant_in.price
                    variant.stock = variant_in.stock
                else:
                    variant = ProductVariant(
                        id=str(generator.get_id()),
                        product_id=product.id,
                        variant_name=variant_in.variant_name,
                        sku=variant_in.sku,
                        price=variant_in.price,
                        stock=variant_in.stock,
                    )
                self.db.add(variant)


            # Clear existing inventory products
            await self.db.execute(
                delete(InventoryProduct).where(InventoryProduct.product_id == product.id)
            )

            # Add updated inventory products based on inventory_ids
            if product_in.inventory_ids:
                for inv_id in product_in.inventory_ids:
                    inventory_product = InventoryProduct(
                        id=str(generator.get_id()),
                        inventory_id=inv_id,
                        product_id=product.id,
                        quantity=0,  # Default or adapt as needed
                        low_stock_threshold=0
                    )
                    self.db.add(inventory_product)

            product.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(product)
            return product
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete(self, product_id: str) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            raise Exception("Product not found")
        try:
            await self.db.delete(product)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e


class ProductVariantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_variant(self,product_id:str,product_name:str, variant_in: ProductVariantCreate) -> ProductVariant:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product variant not found")

        vid=str(generator.get_id())
        sku=generate_sku(product_name, variant_in.variant_name, vid)
        variant = ProductVariant(
            id=vid,
            product_id=product_id,
            sku=sku,
            price=variant_in.price,
            stock=variant_in.stock,
            barcode=str(generate_barcode(json.dumps({
                'id':vid,
                'product_id':product_id,
                'sku':sku,
                'price':variant_in.price,
                'stock':variant_in.stock
                }), 
                logo_path=None, 
                filename=f'{vid}.png', 
                save_as_png=False)
            )
        )

        # Handle attributes
        for attr in variant_in.attributes or []:

            variant.attributes.append(
                ProductVariantAttribute(variant_id=vid,name=attr.name, value=attr.value)
            )

        # Handle images
        for image in variant_in.images or []:
            variant.images.append(
                ProductVariantImage(id=str(generator.get_id()),url=image.url)
            )

        try:
            self.db.add(variant)
            await self.db.commit()
            await self.db.refresh(variant)
            return variant
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_by_id(self, variant_id: str) -> Optional[ProductVariant]:
        result = await self.db.execute(
            select(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .options(
                selectinload(ProductVariant.attributes),
                selectinload(ProductVariant.images)
            )
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        product_id: Optional[str] = None,
        sku: Optional[str] = None,
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
        if min_price is not None:
            filters.append(ProductVariant.price >= min_price)
        if max_price is not None:
            filters.append(ProductVariant.price <= max_price)
        if min_stock is not None:
            filters.append(ProductVariant.stock >= min_stock)

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, variant_id: str, variant_in: ProductVariantUpdate) -> ProductVariant:
        variant = await self.get_by_id(variant_id)
        if not variant:
            raise Exception("Variant not found")

        for field, value in variant_in.dict(exclude_unset=True).items():
            if field == "attributes":
                variant.attributes.clear()
                for attr in value:
                    variant.attributes.append(
                        ProductVariantAttribute(id=str(generator.get_id()),name=attr.name, value=attr.value)
                    )
            elif field == "images":
                variant.images.clear()
                for img in value:
                    variant.images.append(
                        ProductVariantImage(id=str(generator.get_id()),url=img.url)
                    )
            else:
                setattr(variant, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(variant)
            return variant
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete(self, variant_id: str) -> bool:
        variant = await self.get_by_id(variant_id)
        if not variant:
            raise Exception("Variant not found")
        try:
            await self.db.delete(variant)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise e


class ProductVariantAttributeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self,variant_id:str, attr_in: ProductVariantAttributeCreate) -> ProductVariantAttribute:
        attribute = ProductVariantAttribute(
            id=str(generator.get_id()),
            variant_id=variant_id,
            name=attr_in.name,
            value=attr_in.value
        )
        self.db.add(attribute)
        await self.db.commit()
        await self.db.refresh(attribute)
        return attribute

    async def get_by_id(self, attr_id: str) -> Optional[ProductVariantAttribute]:
        result = await self.db.execute(select(ProductVariantAttribute).where(ProductVariantAttribute.id == attr_id))
        return result.scalar_one_or_none()

    async def get_all_by_variant(self, variant_id: str) -> List[ProductVariantAttribute]:
        result = await self.db.execute(select(ProductVariantAttribute).where(ProductVariantAttribute.variant_id == variant_id))
        return result.scalars().all()

    async def update(self, attr_id: str, attr_in: ProductVariantAttributeCreate) -> ProductVariantAttribute:
        attribute = await self.get_by_id(attr_id)
        if not attribute:
            raise Exception("Attribute not found")

        for field, value in attr_in.dict(exclude_unset=True).items():
            setattr(attribute, field, value)

        await self.db.commit()
        await self.db.refresh(attribute)
        return attribute

    async def delete(self, attr_id: str) -> bool:
        attribute = await self.get_by_id(attr_id)
        if not attribute:
            raise Exception("Attribute not found")
        await self.db.delete(attribute)
        await self.db.commit()
        return True


class ProductVariantImageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, variant_id: str, image_in: ProductVariantImageCreate) -> ProductVariantImage:
        image = ProductVariantImage(
            id=str(generator.get_id()),
            variant_id=variant_id,
            url=image_in.url
        )
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def get_by_id(self, image_id: str) -> Optional[ProductVariantImage]:
        result = await self.db.execute(select(ProductVariantImage).where(ProductVariantImage.id == image_id))
        return result.scalar_one_or_none()

    async def get_all_by_variant(self, variant_id: str) -> List[ProductVariantImage]:
        result = await self.db.execute(select(ProductVariantImage).where(ProductVariantImage.variant_id == variant_id))
        return result.scalars().all()

    async def update(self, image_id: str, image_in: ProductVariantImageCreate) -> ProductVariantImage:
        image = await self.get_by_id(image_id)
        if not image:
            raise Exception("Image not found")

        for field, value in image_in.dict(exclude_unset=True).items():
            setattr(image, field, value)

        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def delete(self, image_id: str) -> bool:
        image = await self.get_by_id(image_id)
        if not image:
            raise Exception("Image not found")
        await self.db.delete(image)
        await self.db.commit()
        return True

