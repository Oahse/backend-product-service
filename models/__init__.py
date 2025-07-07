# models/__init__.py
from .products import Tag, Category, Product, ProductImage, ProductVariant, Inventory
# import other models too...

from core.database import Base,engine_db  # or wherever your Base is defined

# Your async function for creating tables
async def create_tables():
    async with engine_db.begin() as conn:
        # Ensure all models are in the Base
        await conn.run_sync(Base.metadata.create_all)

    print("Tables created successfully!")