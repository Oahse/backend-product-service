from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from elasticsearch import AsyncElasticsearch
from core.config import settings

Base = declarative_base()
CHAR_LENGTH=255

# Database engine
SQL_DATABASE_URI = str(settings.SQL_DATABASE_URI) 
ELASTIC_DATABASE_URI = str(settings.ELASTIC_DATABASE_URI) 


engine_db = create_async_engine(SQL_DATABASE_URI, echo=True)

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


# Create a global Elasticsearch instance (singleton)
AsyncElasticDB = AsyncElasticsearch(
    hosts=[ELASTIC_DATABASE_URI],
    verify_certs=False,
    request_timeout=30,
)

async def get_elastic_db():
    try:
        # Ping to check if it's connected
        if not await AsyncElasticDB.ping():
            print("Elasticsearch ping failed.")
            raise ConnectionError("Elasticsearch not available")
        
        print("Elasticsearch connected")
        yield AsyncElasticDB
    except Exception as e:
        print(f"Elasticsearch connection failed: {e}")
        raise
    