from fastapi import FastAPI, Request
from core.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from routes.orders import router as order_router
from routes.payments import router as payment_router
from core.database import get_db 
from core.utils.response import Response, RequestValidationError 
from core.utils.kafka import KafkaConsumer,KafkaProducer ,is_kafka_available
import asyncio, logging


app = FastAPI(
    title="Order and Payment Service API",
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
    db: AsyncSession = Depends(get_db),
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
app.include_router(order_router)
app.include_router(payment_router)

# Basic health endpoint to check if service is running
@app.get("/")
async def read_root():
    return {
        "service": "Order Service API",
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

    except Exception as e:
        logging.critical(f"Failed to start Kafka consumer: {e}")
        await kafka_consumer.stop()
        await kafka_producer.stop()

    
    logging.info("App started")

# FastAPI event handler triggered on application shutdown
@app.on_event("shutdown")
async def shutdown():
    # Stop Kafka consumer gracefully
    await kafka_consumer.stop()
    logging.critical("Kafka consumer stopped.")
    await kafka_producer.stop()
    logging.critical("Kafka producer stopped.")
    
