from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_
from sqlalchemy.orm import selectinload
from fastapi import BackgroundTasks, HTTPException
from typing import List, Optional
from datetime import datetime
from core.database import get_elastic_db
import json
from models.products import UUID, uuid, Product, ProductVariant, ProductVariantImage, ProductVariantAttribute, AvailabilityStatus, Tag, InventoryProduct
from schemas.products import ProductCreate, ProductVariantCreate, ProductVariantUpdate, ProductVariantRead, ProductVariantAttributeCreate, ProductVariantImageCreate
from services.category import CategoryService
from core.config import settings
from core.utils.kafka import KafkaProducer, send_kafka_message, is_kafka_available
from core.utils.barcode import Barcode
from core.utils.file import ImageFile, GoogleDrive  # Assuming your classes are in utils.py

kafka_producer = KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS,
                               topic=str(settings.KAFKA_TOPIC))


def generate_barcode(data, logo_path=None, filename='barcode.png', save_as_png=False):
    barcode = Barcode()
    return barcode.generate_barcode(data=data, logo_path=logo_path, filename=filename, save_as_png=save_as_png)


def generate_sku(product_name: str, variant_name: str, unique_id: UUID) -> str:
    product_code = ''.join(product_name.upper().split())[:3]
    variant_code = ''.join(variant_name.upper().split())[:3]
    suffix = str(unique_id)[-4:].upper()
    sku = f"{product_code}-{variant_code}-{suffix}"
    return sku


async def upload_image_to_drive(base64_str: str, filename: str, quality: int = 30) -> str:
    google_drive = GoogleDrive(jsonkey=settings.google_service_account_info)
    result = google_drive.upload_base64_image_as_webp(
        base64_str=base64_str,
        filename=filename,
        folder_id=None,
        quality=quality
    )
    return result['link']


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

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
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
                raise e

        category = CategoryService(self.db)
        res = await category.get_by_id(product_in.category_id)
        if res is None:
            raise ValueError(f"Invalid category_id: Category with {product_in.category_id} does not exist.")

        pid = uuid.uuid4()
        product = Product(
            id=pid,
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
                vid = uuid.uuid4()
                sku = generate_sku(product_in.name, variant_in.variant_name, vid)
                barcode_data = json.dumps({
                    'id': str(vid),
                    'product_id': str(pid),
                    'sku': sku,
                    'price': variant_in.price,
                    'stock': variant_in.stock
                })
                barcode_str = str(generate_barcode(barcode_data, filename=f'{vid}.png'))

                variant = ProductVariant(
                    id=vid,
                    product_id=pid,
                    sku=sku,
                    price=variant_in.price,
                    stock=variant_in.stock,
                    barcode=barcode_str,
                    variant_name=variant_in.variant_name,
                )
                self.db.add(variant)

                # Upload images and add them
                for i, image in enumerate(variant_in.images or []):
                    url = await upload_image_to_drive(image, f"{vid}_{i}.webp", quality=30)
                    v_image = ProductVariantImage(
                        variant_id=vid,
                        url=url,
                        alt_text=sku
                    )
                    self.db.add(v_image)

            # Handle inventory ids
            if product_in.inventory_ids:
                for inv_id in product_in.inventory_ids:
                    inventory_product = InventoryProduct(
                        inventory_id=inv_id,
                        product_id=pid,
                        quantity=0,  # default quantity
                        low_stock_threshold=0
                    )
                    self.db.add(inventory_product)

            await self.db.commit()

            # Reload product with relationships eagerly loaded
            product = await self.get_by_id(pid)
            if not product:
                raise Exception("Product not found after creation")
            return product

        except Exception as e:
            await self.db.rollback()
            raise e

    async def update(self, product_id: UUID, product_in: ProductCreate) -> Product:
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

            incoming_variant_ids = {v.id for v in (product_in.variants or []) if getattr(v, "id", None)}
            existing_variants = {v.id: v for v in product.variants}

            # Delete removed variants
            for variant_id in list(existing_variants.keys()):
                if variant_id not in incoming_variant_ids:
                    await self.db.delete(existing_variants[variant_id])

            # Add or update variants
            for variant_in in product_in.variants or []:
                if getattr(variant_in, "id", None) in existing_variants:
                    variant = existing_variants[variant_in.id]
                    variant.price = variant_in.price
                    variant.stock = variant_in.stock
                    variant.variant_name = variant_in.variant_name

                    # Remove existing images, re-add new ones (simplified logic)
                    await self.db.execute(delete(ProductVariantImage).where(ProductVariantImage.variant_id == variant.id))
                    for i, image in enumerate(variant_in.images or []):
                        url = await upload_image_to_drive(image, f"{variant.id}_{i}.webp", quality=30)
                        v_image = ProductVariantImage(
                            variant_id=variant.id,
                            url=url,
                            alt_text=variant.sku
                        )
                        self.db.add(v_image)
                else:
                    vid = uuid.uuid4()
                    sku = generate_sku(product.name, variant_in.variant_name, vid)
                    barcode_data = json.dumps({
                        'id': str(vid),
                        'product_id': str(product_id),
                        'sku': sku,
                        'price': variant_in.price,
                        'stock': variant_in.stock
                    })
                    barcode_str = str(generate_barcode(barcode_data, filename=f'{vid}.png'))
                    variant = ProductVariant(
                        id=vid,
                        product_id=product_id,
                        sku=sku,
                        price=variant_in.price,
                        stock=variant_in.stock,
                        barcode=barcode_str,
                        variant_name=variant_in.variant_name,
                    )
                    self.db.add(variant)

                    for i, image in enumerate(variant_in.images or []):
                        url = await upload_image_to_drive(image, f"{vid}_{i}.webp", quality=30)
                        v_image = ProductVariantImage(
                            variant_id=vid,
                            url=url,
                            alt_text=sku
                        )
                        self.db.add(v_image)

            # Update inventories associations similarly if needed

            await self.db.commit()
            product = await self.get_by_id(product_id)
            return product
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete(self, product_id: UUID) -> None:
        product = await self.get_by_id(product_id)
        if not product:
            raise Exception("Product not found")
        try:
            await self.db.delete(product)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            raise e

