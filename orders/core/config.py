import os
from typing import Any, List, Literal
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,  # Show all messages from DEBUG and up
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Load environment variables from .env file located in the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)


def parse_cors(value: str) -> List[str]:
    """
    Parses CORS origins. Accepts comma-separated string or list-like string.
    Example: "http://localhost,http://127.0.0.1" → ["http://localhost", "http://127.0.0.1"]
    """
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            return [i.strip().strip("'\"") for i in value[1:-1].split(",")]
        return [i.strip() for i in value.split(",")]
    raise ValueError("Invalid CORS format")

class Settings:
    # Environment
    DOMAIN: str = os.getenv('DOMAIN', 'localhost')
    ENVIRONMENT: Literal["local", "staging", "production"] = os.getenv('ENVIRONMENT', 'local')

    KAFKA_BOOTSTRAP_SERVERS : List[str] = parse_cors(os.getenv('KAFKA_BOOTSTRAP_SERVERS', "[localhost:9092]"))
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC', 'orders_topic')
    KAFKA_GROUP: str = os.getenv('KAFKA_GROUP', 'orders_group')
    KAFKA_HOST: str = os.getenv('KAFKA_HOST', 'kafka')
    KAFKA_PORT: str = os.getenv('KAFKA_PORT', '9092')
    
    # PostgreSQL
    POSTGRES_DB: str = os.getenv('POSTGRES_DB','postgresql+asyncpg://postgres:postgres@postgres:5432/users_db')

    # SQLite (fallback if needed)
    SQLITE_DB_PATH: str = os.getenv('SQLITE_DB_PATH', 'db1.db')

    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'changeme-super-secret-key')

    # CORS
    RAW_CORS_ORIGINS: str = os.getenv('BACKEND_CORS_ORIGINS', '')
    BACKEND_CORS_ORIGINS: List[str] = parse_cors(RAW_CORS_ORIGINS)

    @property
    def server_host(self) -> str:
        return f"http://{self.DOMAIN}" if self.ENVIRONMENT == "local" else f"https://{self.DOMAIN}"

    @property
    def SQL_DATABASE_URI(self) -> str:
        if self.ENVIRONMENT in ["local"]:
            # return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"  # SQLite URI
            return self.POSTGRES_DB
        
        elif self.ENVIRONMENT in ["staging", "production"]:
            # for docker
            # return 'postgresql+asyncpg://postgres:postgres@users-db:5432/users_db'

            # for render
            return self.POSTGRES_DB
        else:
            raise ValueError("Invalid ENVIRONMENT for database connection")

# Instantiate the settings object
settings = Settings()


