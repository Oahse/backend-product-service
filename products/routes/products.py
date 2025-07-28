from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.database import get_db, get_elastic_db
from services.products import ProductService, ProductVariantService,ProductVariantAttributeService, ProductVariantImageService
from schemas.products import ProductCreate, ProductVariantCreate, ProductVariantUpdate,ProductVariantAttributeCreate,ProductVariantImageCreate
from core.utils.response import Response
from models.products import AvailabilityStatus

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

@router.get("/search")
async def search_products(
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
    db: AsyncSession = Depends(get_db),
):
    esclient = await get_elastic_db()
    service = ProductService(db, esclient)
    try:
        result = await service.search(q, name, category_id, tag_id, availability,
                                      min_price, max_price, min_rating, limit, offset)
        return Response(data=result)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/")
async def get_all_products(
    name: Optional[str] = None,
    category_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    availability: Optional[AvailabilityStatus] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    esclient = await get_elastic_db()
    service = ProductService(db, esclient)
    try:
        products = await service.get_all(
            name, category_id, tag_id, availability,
            min_price, max_price, min_rating, limit, offset
        )
        return Response(data=[p.to_dict() for p in products])
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/{product_id}")
async def get_product_by_id(product_id: str, db: AsyncSession = Depends(get_db)):
    
    esclient = await get_elastic_db()
    service = ProductService(db, esclient)
    try:
        product = await service.get_by_id(product_id)
        if not product:
            return Response(success=False, message=f"Product with id '{product_id}' not found.", code=404)
        return Response(data=product.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    esclient = await get_elastic_db()
    service = ProductService(db, esclient)

    try:
        product = await service.create(product_in)
        return Response(data=product.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.put("/{product_id}")
async def update_product(product_id: str, product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    esclient = await get_elastic_db()
    service = ProductService(db, esclient)
    try:
        product = await service.update(product_id, product_in)
        if not product:
            return Response(success=False, message=f"Product with id '{product_id}' not found.", code=404)
        return Response(data=product.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str, db: AsyncSession = Depends(get_db)):
    esclient = await get_elastic_db()
    service = ProductService(db, esclient)
    try:
        res = await service.delete(product_id)
        if not res:
            return Response(success=False, message=f"Product with id '{product_id}' not found.", code=404)
        return Response(message="Product deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)

@router.get("/variants/")
async def get_all_variants(
    product_id: Optional[str] = None,
    sku: Optional[str] = None,
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
            product_id=product_id,
            sku=sku,
            min_price=min_price,
            max_price=max_price,
            min_stock=min_stock,
            limit=limit,
            offset=offset,
        )
        return Response(data=[v.to_dict() for v in variants])
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/variants/{variant_id}")
async def get_variant_by_id(variant_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        variant = await service.get_by_id(variant_id)
        if not variant:
            return Response(success=False, message=f"Variant with id '{variant_id}' not found.", code=404)
        return Response(data=variant.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.post("/variants/", status_code=status.HTTP_201_CREATED)
async def create_variant(product_id:str,product_name:str, variant_in: ProductVariantCreate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        variant = await service.add_variant(product_id,product_name, variant_in)
        return Response(data=variant.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.put("/variants/{variant_id}")
async def update_variant(variant_id: str, variant_in: ProductVariantUpdate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        variant = await service.update(variant_id, variant_in)
        if not variant:
            return Response(success=False, message=f"Variant with id '{variant_id}' not found.", code=404)
        return Response(data=variant.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.delete("/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(variant_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantService(db)
    try:
        res = await service.delete(variant_id)
        if not res:
            return Response(success=False, message=f"Variant with id '{variant_id}' not found.", code=404)
        return Response(message="Variant deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


### Variant Attributes ###

@router.post("/variants/{variant_id}/attributes/", status_code=status.HTTP_201_CREATED)
async def create_variant_attribute(variant_id:str,attr_in: ProductVariantAttributeCreate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantAttributeService(db)
    try:
        attribute = await service.create(variant_id,attr_in)
        return Response(data=attribute.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/attributes/{attr_id}")
async def get_variant_attribute(attr_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantAttributeService(db)
    try:
        attr = await service.get_by_id(attr_id)
        if not attr:
            return Response(success=False, message=f"Attribute with id '{attr_id}' not found.", code=404)
        return Response(data=attr.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/variants/{variant_id}/attributes/")
async def list_variant_attributes(variant_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantAttributeService(db)
    try:
        attrs = await service.get_all_by_variant(variant_id)
        return Response(data=[a.to_dict() for a in attrs])
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.put("/attributes/{attr_id}")
async def update_variant_attribute(attr_id: str, attr_in: ProductVariantAttributeCreate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantAttributeService(db)
    try:
        attr = await service.update(attr_id, attr_in)
        if not attr:
            return Response(success=False, message=f"Attribute with id '{attr_id}' not found.", code=404)
        return Response(data=attr.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.delete("/attributes/{attr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant_attribute(attr_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantAttributeService(db)
    try:
        res = await service.delete(attr_id)
        if not res:
            return Response(success=False, message=f"Attribute with id '{attr_id}' not found.", code=404)
        return Response(message="Attribute deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


### Variant Images ###

@router.post("/variants/{variant_id}/images/", status_code=status.HTTP_201_CREATED)
async def create_variant_image(variant_id: str, image_in: ProductVariantImageCreate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantImageService(db)
    try:
        image = await service.create(variant_id, image_in)
        return Response(data=image.to_dict(), code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/images/{image_id}")
async def get_variant_image(image_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantImageService(db)
    try:
        image = await service.get_by_id(image_id)
        if not image:
            return Response(success=False, message=f"Image with id '{image_id}' not found.", code=404)
        return Response(data=image.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.get("/variants/{variant_id}/images/")
async def list_variant_images(variant_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantImageService(db)
    try:
        images = await service.get_all_by_variant(variant_id)
        return Response(data=[i.to_dict() for i in images])
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.put("/images/{image_id}")
async def update_variant_image(image_id: str, image_in: ProductVariantImageCreate, db: AsyncSession = Depends(get_db)):
    service = ProductVariantImageService(db)
    try:
        image = await service.update(image_id, image_in)
        if not image:
            return Response(success=False, message=f"Image with id '{image_id}' not found.", code=404)
        return Response(data=image.to_dict())
    except Exception as e:
        return Response(success=False, message=str(e), code=500)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant_image(image_id: str, db: AsyncSession = Depends(get_db)):
    service = ProductVariantImageService(db)
    try:
        res = await service.delete(image_id)
        if not res:
            return Response(success=False, message=f"Image with id '{image_id}' not found.", code=404)
        return Response(message="Image deleted successfully", code=204)
    except Exception as e:
        return Response(success=False, message=str(e), code=500)
