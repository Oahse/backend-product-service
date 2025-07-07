from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError,NoResultFound
from sqlalchemy import update, delete
from sqlalchemy import and_, or_
from core.utils.encryption import PasswordManager
from typing import List, Optional
from core.utils.generator import generator
import uuid
from datetime import datetime, timedelta

from models.products import (
    Product, ProductVariant, Inventory, ProductImage,
    Category, Tag, PromoCode,AvailabilityStatus, InventoryProduct
)
from schemas.products import (
    ProductCreate, ProductRead, ProductVariantCreate,ProductVariantUpdate, ProductVariantRead,
    InventoryCreate, InventoryRead, InventoryProductCreate, InventoryProductRead, InventoryProductReadWithProduct, InventoryProductUpdate, InventoryUpdate, ProductImageCreate, ProductImageRead,
    CategoryCreate, CategoryRead, TagCreate, TagRead, PromoCodeCreate, PromoCodeRead,
)



class ProductService:
    def __init__(self, db: AsyncSession):  
        self.db = db
    
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
            query = query.distinct()  # Prevent duplicates from join

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def create(self, product_in: ProductCreate) -> Product:
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
        return product

    async def update(self, product_id: int, product_in: ProductCreate) -> Optional[Product]:
        product = await self.get_by_id(product_id)
        if not product:
            return None

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

        # Update variants
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

        # Images
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

        # Add updated ones
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

    async def delete(self, product_id: int) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False
        await self.db.delete(product)
        await self.db.commit()
        return True

class ProductVariantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_variant(self, product_id: int, variant_in: ProductVariantCreate) -> Optional[ProductVariant]:
        variant = ProductVariant(
            product_id=product_id,
            variant_name=variant_in.variant_name,
            sku=variant_in.sku,
            price=variant_in.price,
            stock=variant_in.stock,
        )
        self.db.add(variant)
        await self.db.commit()
        await self.db.refresh(variant)
        return variant

    async def get_by_id(self, variant_id: int) -> Optional[ProductVariant]:
        result = await self.db.execute(select(ProductVariant).where(ProductVariant.id == variant_id))
        return result.scalar_one_or_none()

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

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, variant_id: int, variant_in: ProductVariantUpdate) -> Optional[ProductVariant]:
        variant = await self.get_by_id(variant_id)
        if not variant:
            return None
        for field, value in variant_in.dict(exclude_unset=True).items():
            setattr(variant, field, value)
        await self.db.commit()
        await self.db.refresh(variant)
        return variant

    async def delete(self, variant_id: int) -> bool:
        variant = await self.get_by_id(variant_id)
        if not variant:
            return False
        await self.db.delete(variant)
        await self.db.commit()
        return True

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        name: Optional[str] = None,
        description_contains: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Category]:
        query = select(Category)
        filters = []

        if name:
            filters.append(Category.name.ilike(f"%{name}%"))
        if description_contains:
            filters.append(Category.description.ilike(f"%{description_contains}%"))

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, category_id: int) -> Optional[Category]:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def create(self, category_in: CategoryCreate) -> Category:
        category = Category(
            id=str(generator.get_id()),
            name=category_in.name,
            description=category_in.description,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: int, category_in: CategoryCreate) -> Optional[Category]:
        category = await self.get_by_id(category_id)
        if not category:
            return None
        category.name = category_in.name
        category.description = category_in.description
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:
        category = await self.get_by_id(category_id)
        if not category:
            return False
        await self.db.delete(category)
        await self.db.commit()
        return True


class TagService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        name: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Tag]:
        query = select(Tag)

        if name:
            query = query.where(Tag.name.ilike(f"%{name}%"))

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, tag_id: int) -> Optional[Tag]:
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def create(self, tag_in: TagCreate) -> Tag:
        tag = Tag(id=str(generator.get_id()), name=tag_in.name)
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def update(self, tag_id: int, tag_in: TagCreate) -> Optional[Tag]:
        tag = await self.get_by_id(tag_id)
        if not tag:
            return None
        tag.name = tag_in.name
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def delete(self, tag_id: int) -> bool:
        tag = await self.get_by_id(tag_id)
        if not tag:
            return False
        await self.db.delete(tag)
        await self.db.commit()
        return True


class PromoCodeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        active: Optional[bool] = None,
        valid_on: Optional[datetime] = None,
        code_contains: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[PromoCode]:
        query = select(PromoCode)
        filters = []

        if active is not None:
            filters.append(PromoCode.active == active)
        if valid_on:
            filters.append(PromoCode.valid_from <= valid_on)
            filters.append(PromoCode.valid_until >= valid_on)
        if code_contains:
            filters.append(PromoCode.code.ilike(f"%{code_contains}%"))

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_id(self, promo_code_id: int) -> Optional[PromoCode]:
        result = await self.db.execute(select(PromoCode).where(PromoCode.id == promo_code_id))
        return result.scalar_one_or_none()

    async def create(self, promo_in: PromoCodeCreate) -> PromoCode:
        promo = PromoCode(
            id=str(generator.get_id()),
            code=promo_in.code,
            discount_percent=promo_in.discount_percent,
            active=promo_in.active,
            valid_from=promo_in.valid_from,
            valid_until=promo_in.valid_until
        )
        self.db.add(promo)
        await self.db.commit()
        await self.db.refresh(promo)
        return promo

    async def update(self, promo_code_id: int, promo_in: PromoCodeCreate) -> Optional[PromoCode]:
        promo = await self.get_by_id(promo_code_id)
        if not promo:
            return None
        promo.code = promo_in.code
        promo.discount_percent = promo_in.discount_percent
        promo.active = promo_in.active
        promo.valid_from = promo_in.valid_from
        promo.valid_until = promo_in.valid_until
        await self.db.commit()
        await self.db.refresh(promo)
        return promo

    async def delete(self, promo_code_id: int) -> bool:
        promo = await self.get_by_id(promo_code_id)
        if not promo:
            return False
        await self.db.delete(promo)
        await self.db.commit()
        return True

class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        name: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Inventory]:
        query = select(Inventory)
        filters = []

        if name:
            filters.append(Inventory.name.ilike(f"%{name}%"))
        if location:
            filters.append(Inventory.location.ilike(f"%{location}%"))

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, inventory_id: str) -> Optional[Inventory]:
        result = await self.db.execute(select(Inventory).where(Inventory.id == inventory_id))
        return result.scalar_one_or_none()

    async def create(self, inventory_in: InventoryCreate) -> Inventory:
        inventory = Inventory(
            id=str(generator.get_id()),
            name=inventory_in.name,
            location=inventory_in.location
        )
        self.db.add(inventory)
        await self.db.commit()
        await self.db.refresh(inventory)
        return inventory

    async def update(self, inventory_id: str, inventory_in: InventoryCreate) -> Optional[Inventory]:
        inventory = await self.get_by_id(inventory_id)
        if not inventory:
            return None
        inventory.name = inventory_in.name
        inventory.location = inventory_in.location
        await self.db.commit()
        await self.db.refresh(inventory)
        return inventory

    async def delete(self, inventory_id: str) -> bool:
        inventory = await self.get_by_id(inventory_id)
        if not inventory:
            return False
        await self.db.delete(inventory)
        await self.db.commit()
        return True


class InventoryProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        inventory_id: Optional[str] = None,
        product_id: Optional[str] = None,
        min_quantity: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[InventoryProduct]:
        query = select(InventoryProduct)
        filters = []

        if inventory_id:
            filters.append(InventoryProduct.inventory_id == inventory_id)
        if product_id:
            filters.append(InventoryProduct.product_id == product_id)
        if min_quantity is not None:
            filters.append(InventoryProduct.quantity >= min_quantity)

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, entry_id: str) -> Optional[InventoryProduct]:
        result = await self.db.execute(select(InventoryProduct).where(InventoryProduct.id == entry_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        inventory_id: str,
        product_id: str,
        quantity: int = 0,
        low_stock_threshold: int = 5
    ) -> InventoryProduct:
        entry = InventoryProduct(
            id=str(generator.get_id()),
            inventory_id=inventory_id,
            product_id=product_id,
            quantity=quantity,
            low_stock_threshold=low_stock_threshold
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def update(
        self,
        entry_id: str,
        quantity: Optional[int] = None,
        low_stock_threshold: Optional[int] = None
    ) -> Optional[InventoryProduct]:
        entry = await self.get_by_id(entry_id)
        if not entry:
            return None

        if quantity is not None:
            entry.quantity = quantity
        if low_stock_threshold is not None:
            entry.low_stock_threshold = low_stock_threshold

        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete(self, entry_id: str) -> bool:
        entry = await self.get_by_id(entry_id)
        if not entry:
            return False
        await self.db.delete(entry)
        await self.db.commit()
        return True