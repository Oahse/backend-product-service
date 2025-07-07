from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError,NoResultFound
from sqlalchemy import update, delete
from core.utils.encryption import PasswordManager
from typing import List, Optional
from core.utils.generator import generator
import uuid
from datetime import datetime, timedelta

from models.products import (
    Product, ProductVariant, Inventory, ProductImage,
    Category, Tag, PromoCode
)
from schemas.products import (
    ProductCreate, ProductRead, ProductVariantCreate, ProductVariantRead,
    InventoryCreate, InventoryRead, ProductImageCreate, ProductImageRead,
    CategoryCreate, CategoryRead, TagCreate, TagRead, PromoCodeCreate, PromoCodeRead
)

def generate_activation_token():
    return str(uuid.uuid4())  # or another secure token generator

def generate_activation_expiry(hours=24):
    return datetime.utcnow() + timedelta(hours=hours)




class ProductService:
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Product]:
        result = await session.execute(select(Product))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, product_id: int) -> Optional[Product]:
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, product_in: ProductCreate) -> Product:
        # Fetch tags by ids
        tags = []
        if product_in.tag_ids:
            result = await session.execute(select(Tag).where(Tag.id.in_(product_in.tag_ids)))
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
        session.add(product)
        await session.flush()  # get product.id for relations

        # Create variants
        for variant_in in product_in.variants or []:
            variant = ProductVariant(
                product_id=product.id,
                variant_name=variant_in.variant_name,
                sku=variant_in.sku,
                price=variant_in.price,
                stock=variant_in.stock,
            )
            session.add(variant)

        # Create images
        for image_in in product_in.images or []:
            image = ProductImage(
                product_id=product.id,
                url=image_in.url,
                alt_text=image_in.alt_text,
                is_primary=image_in.is_primary,
            )
            session.add(image)

        # Create inventory
        if product_in.inventory:
            inventory = Inventory(
                product_id=product.id,
                quantity=product_in.inventory.quantity,
                low_stock_threshold=product_in.inventory.low_stock_threshold,
            )
            session.add(inventory)

        await session.commit()
        await session.refresh(product)
        return product

    @staticmethod
    async def update(session: AsyncSession, product_id: int, product_in: ProductCreate) -> Optional[Product]:
        product = await ProductService.get_by_id(session, product_id)
        if not product:
            return None

        # Update main fields
        product.name = product_in.name
        product.sku = product_in.sku
        product.description = product_in.description
        product.base_price = product_in.base_price
        product.sale_price = product_in.sale_price
        product.availability = product_in.availability
        product.rating = product_in.rating or product.rating
        product.category_id = product_in.category_id

        # Update tags
        if product_in.tag_ids is not None:
            result = await session.execute(select(Tag).where(Tag.id.in_(product_in.tag_ids)))
            product.tags = result.scalars().all()

        # Variants update/delete/add can be handled here (complex logic)
        # For brevity, skipping detailed variant update logic here

        # Similarly, images and inventory updates can be added

        product.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(product)
        return product

    @staticmethod
    async def delete(session: AsyncSession, product_id: int) -> bool:
        product = await ProductService.get_by_id(session, product_id)
        if not product:
            return False
        await session.delete(product)
        await session.commit()
        return True


class CategoryService:
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Category]:
        result = await session.execute(select(Category))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, category_id: int) -> Optional[Category]:
        result = await session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, category_in: CategoryCreate) -> Category:
        category = Category(
            id=str(generator.get_id()),
            name=category_in.name,
            description=category_in.description
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def update(session: AsyncSession, category_id: int, category_in: CategoryCreate) -> Optional[Category]:
        category = await CategoryService.get_by_id(session, category_id)
        if not category:
            return None
        category.name = category_in.name
        category.description = category_in.description
        await session.commit()
        await session.refresh(category)
        return category

    @staticmethod
    async def delete(session: AsyncSession, category_id: int) -> bool:
        category = await CategoryService.get_by_id(session, category_id)
        if not category:
            return False
        await session.delete(category)
        await session.commit()
        return True


class TagService:
    @staticmethod
    async def get_all(session: AsyncSession) -> List[Tag]:
        result = await session.execute(select(Tag))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, tag_id: int) -> Optional[Tag]:
        result = await session.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, tag_in: TagCreate) -> Tag:
        tag = Tag(id=str(generator.get_id()),name=tag_in.name)
        session.add(tag)
        await session.commit()
        await session.refresh(tag)
        return tag

    @staticmethod
    async def update(session: AsyncSession, tag_id: int, tag_in: TagCreate) -> Optional[Tag]:
        tag = await TagService.get_by_id(session, tag_id)
        if not tag:
            return None
        tag.name = tag_in.name
        await session.commit()
        await session.refresh(tag)
        return tag

    @staticmethod
    async def delete(session: AsyncSession, tag_id: int) -> bool:
        tag = await TagService.get_by_id(session, tag_id)
        if not tag:
            return False
        await session.delete(tag)
        await session.commit()
        return True


class PromoCodeService:
    @staticmethod
    async def get_all(session: AsyncSession) -> List[PromoCode]:
        result = await session.execute(select(PromoCode))
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, promo_code_id: int) -> Optional[PromoCode]:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_code_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, promo_in: PromoCodeCreate) -> PromoCode:
        promo = PromoCode(
            id=str(generator.get_id()),
            code=promo_in.code,
            discount_percent=promo_in.discount_percent,
            active=promo_in.active,
            valid_from=promo_in.valid_from,
            valid_until=promo_in.valid_until
        )
        session.add(promo)
        await session.commit()
        await session.refresh(promo)
        return promo

    @staticmethod
    async def update(session: AsyncSession, promo_code_id: int, promo_in: PromoCodeCreate) -> Optional[PromoCode]:
        promo = await PromoCodeService.get_by_id(session, promo_code_id)
        if not promo:
            return None
        promo.code = promo_in.code
        promo.discount_percent = promo_in.discount_percent
        promo.active = promo_in.active
        promo.valid_from = promo_in.valid_from
        promo.valid_until = promo_in.valid_until
        await session.commit()
        await session.refresh(promo)
        return promo

    @staticmethod
    async def delete(session: AsyncSession, promo_code_id: int) -> bool:
        promo = await PromoCodeService.get_by_id(session, promo_code_id)
        if not promo:
            return False
        await session.delete(promo)
        await session.commit()
        return True
