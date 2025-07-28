from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from elasticsearch import AsyncElasticsearch, Elasticsearch
from core.config import settings,logging
import asyncio
Base = declarative_base()
CHAR_LENGTH=255

# Database engine
SQL_DATABASE_URI = str(settings.SQL_DATABASE_URI) 
ELASTIC_DATABASE_URI = str(settings.ELASTIC_DATABASE_URI) 


engine_db = create_async_engine(SQL_DATABASE_URI, echo=True, pool_pre_ping=True)

# Session factory for the first database (Async)
AsyncSessionDB = sessionmaker(
    bind=engine_db, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency to get the async session for the first database
async def get_db():
    try:
        async with AsyncSessionDB() as session:
            logging.info(f"Database connected")
            yield session
    except Exception as e:
        # Log the error or handle it accordingly
        logging.critical(f"Database connection failed: {e}")
        raise


async def get_elastic_db():
    """
    Dependency that yields an Elasticsearch client.
    Retries connection attempts up to 5 times.
    """
    try:
        logging.info(f"[Elasticsearch] Attempting to connect to {ELASTIC_DATABASE_URI}...")
        # Singleton instance (do not recreate per request)
        AsyncElasticDB = AsyncElasticsearch(
            hosts=[ELASTIC_DATABASE_URI],
            verify_certs=False,
            request_timeout=30,
        )
        logging.info("[Elasticsearch] Connected successfully.")
        return AsyncElasticDB
        
    except Exception as e:
        raise ConnectionError(f"[Elasticsearch] connection failed: {e}") 


def get_elastic_db_sync():
    """
    Returns a synchronous Elasticsearch client instance.
    """
    try:
        logging.info(f"[Elasticsearch] Attempting to connect to {ELASTIC_DATABASE_URI}...")
        es = Elasticsearch(
            [ELASTIC_DATABASE_URI],
            verify_certs=False,
            timeout=30
        )
        logging.info("[Elasticsearch] Connected successfully.")
        return es
    except Exception as e:
        logging.critical(f"[Elasticsearch] Connection failed: {e}")
        raise
    