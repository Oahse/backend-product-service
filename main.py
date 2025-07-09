from fastapi import FastAPI, Request
from core.config import Settings
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from core.database import get_elastic_db,get_elastic_db_sync # Your async Elasticsearch instance
from routes.products import router as product_router
from routes.category import router as category_router
from routes.inventory import router as inventory_router
from routes.promocode import router as promocode_router
from routes.tag import router as tag_router
from core.utils.response import Response, RequestValidationError 
from core.utils.kafka import KafkaConsumer,KafkaProducer ,is_kafka_available
import asyncio


app = FastAPI(
    title="Product Service API",
    description="Handles Product operations.",
    version="1.0.0"
)

# Load settings/configuration from your core config module
settings = Settings()

# Initialize Kafka consumer with broker(s), topic and group ID from settings
kafka_consumer = KafkaConsumer(
    broker=",".join(settings.KAFKA_BOOTSTRAP_SERVERS),
    topic=str(settings.KAFKA_TOPIC),
    group_id=str(settings.KAFKA_GROUP),
    es=get_elastic_db_sync()
)

kafka_producer = KafkaProducer(broker=settings.KAFKA_BOOTSTRAP_SERVERS,
                                topic=str(settings.KAFKA_TOPIC))

consumer_task = None  # This will hold the asyncio task for consuming Kafka messages

# Setup CORS middleware if BACKEND_CORS_ORIGINS is configured in settings
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware to manage client sessions with your secret key
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Register all routers (API route groups) for different resources
app.include_router(product_router)
app.include_router(category_router)
app.include_router(inventory_router)
app.include_router(promocode_router)
app.include_router(tag_router)

# Basic health endpoint to check if service is running
@app.get("/")
async def read_root():
    return {
        "service": "Products Service API",
        "status": "Running",
        "version": "1.0.0"
    }

# Global handler for request validation errors to return consistent error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        e = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
        }
        if "ctx" in error:
            e["ctx"] = error["ctx"]
        errors.append(e)

    # Return single error object if only one error, else return list of errors
    message = errors[0] if len(errors) == 1 else errors

    return Response(message=message, success=False, code=422)

# FastAPI event handler triggered on application startup


@app.on_event("startup")
async def startup():
    global consumer_task
    kafka_host = settings.KAFKA_HOST
    kafka_port = int(settings.KAFKA_PORT)
    try:
        await kafka_consumer.start()
        consumer_task = asyncio.create_task(kafka_consumer.consume())

        print("Kafka consumer started.")
        await kafka_producer.start()
        await kafka_producer.send({
            "product": {"id": "abc123", "name": "Test Product"},
            "action": "create"
        })

    except Exception as e:
        print(f"Failed to start Kafka consumer: {e}")
        await kafka_consumer.stop()
    try:
        esclient = await get_elastic_db()
        await esclient.info()
    except Exception as e:
        print(f"Failed to start elastic search db: {e}")


# FastAPI event handler triggered on application shutdown
@app.on_event("shutdown")
async def shutdown():
    # Stop Kafka consumer gracefully
    await kafka_consumer.stop()
    print("Kafka consumer stopped.")
    
