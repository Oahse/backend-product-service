from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db,get_elastic_db
from services.products import ProductService,ProductVariantService,AsyncElasticsearch
from schemas.products import ProductCreate,ProductVariantCreate, ProductVariantUpdate
from core.utils.response import Response
from models.products import AvailabilityStatus


router = APIRouter(prefix="/api/v1/products", tags=["Products"])

@router.get("/search")
async def search_products(
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
        es: AsyncElasticsearch = Depends(get_elastic_db)
    ):
    service = ProductService(es)
    try:
        
        result = await service.search(q, name, sku, category_id, tag_id, availability, min_price, max_price, min_rating, limit, offset)
        return Response(data=result )
    except Exception as e:
        return Response(data=str(e), code=500)

@router.get("/")
async def get_all_products(
    name: Optional[str] = None,
    sku: Optional[str] = None,
    category_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    availability: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_elastic_db)
):
    service = ProductService(db,es)
    try:
        products = await service.get_all(
            name, sku, category_id, tag_id, availability,
            min_price, max_price, min_rating, limit, offset
        )
        return Response(data=[p.to_dict() for p in products])
    except Exception as e:
        return Response(data=str(e), code=500)


@router.get("/{product_id}")
async def get_product_by_id(product_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    try:
        product = await service.get_by_id(product_id)
        if product is None:
            return Response(message=f"Product with id '{product_id}' not found.", code=404)
        return Response(data=product.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    try:
        product = await service.create(product_in)
        return Response(data=product.to_dict(), code=201)
    except Exception as e:
        return Response(data=str(e), code=500)


@router.put("/{product_id}")
async def update_product(product_id: int, product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    try:
        product = await service.update(product_id, product_in)
        if product is None:
            return Response(message=f"Product with id '{product_id}' not found.", code=404)
        return Response(data=product.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)
    try:
        res = await service.delete(product_id)
        if not res:
            return Response(message=f"Product with id '{product_id}' not found.", code=404)
        return Response(message="Product deleted successfully", code=204)
    except Exception as e:
        return Response(data=str(e), code=500)



@router.get("/variants/")
async def get_all_variants(
    product_id: Optional[str] = None,
    sku: Optional[str] = None,
    variant_name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_stock: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    service = ProductVariantService(db)
    try:
        variants = await service.get_all(
            product_id, sku, variant_name, min_price, max_price, min_stock, limit, offset
        )
        return Response(data=[v.to_dict() for v in variants])
    except Exception as e:
        return Response(data=str(e), code=500)


@router.get("/variants/{variant_id}")
async def get_variant_by_id(variant_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        variant = await service.get_by_id(variant_id)
        if variant is None:
            return Response(message=f"Variant with id '{variant_id}' not found.", code=404)
        return Response(data=variant.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.post("/variants/", status_code=status.HTTP_201_CREATED)
async def create_variant(variant_in: ProductVariantCreate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        variant = await service.add_variant(variant_in.product_id, variant_in)
        return Response(data=variant.to_dict(), code=201)
    except Exception as e:
        return Response(data=str(e), code=500)


@router.put("/variants/{variant_id}")
async def update_variant(variant_id: int, variant_in: ProductVariantUpdate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        variant = await service.update(variant_id, variant_in)
        if variant is None:
            return Response(message=f"Variant with id '{variant_id}' not found.", code=404)
        return Response(data=variant.to_dict())
    except Exception as e:
        return Response(data=str(e), code=500)


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(variant_id: int, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        res = await service.delete(variant_id)
        if not res:
            return Response(message=f"Variant with id '{variant_id}' not found.", code=404)
        return Response(message="Variant deleted successfully", code=204)
    except Exception as e:
        return Response(data=str(e), code=500)
