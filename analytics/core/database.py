from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from core.config import settings

Base = declarative_base()
CHAR_LENGTH=255

# Database engine
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI) 
# print(SQLALCHEMY_DATABASE_URL,'------')
# print(str(settings.ENVIRONMENT),'environment')

engine_db = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Session factory for the first database (Async)
AsyncSessionDB = sessionmaker(
    bind=engine_db, 
    class_=AsyncSession, 
    expire_on_commit=True, 
    pool_pre_ping=True  # ensures connection is alive before use
)


# Dependency to get the async session for the first database
async def get_db():
    try:
        async with AsyncSessionDB() as session:
            print(f"Database connected")
            yield session
    except Exception as e:
        # Log the error or handle it accordingly
        print(f"Database connection failed: {e}")
        raise
