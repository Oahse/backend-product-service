import os
from typing import Any, List, Literal
from dotenv import load_dotenv
import logging, json

logging.basicConfig(
    level=logging.DEBUG,  # Show all messages from DEBUG and up
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
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC', 'products_topic')
    KAFKA_GROUP: str = os.getenv('KAFKA_GROUP', 'product_group')
    KAFKA_HOST: str = os.getenv('KAFKA_HOST', 'kafka')
    KAFKA_PORT: str = os.getenv('KAFKA_PORT', '9092')
    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://default:4kZH1STNfGDscS29dCdbU7nJMPrDLZfh@redis-10990.c52.us-east-1-4.ec2.redns.redis-cloud.com:10990')
    
    ELASTIC_DB: str = os.getenv('ELASTIC_DB', "http://elasticsearch:9200")

    # PostgreSQL
    POSTGRES_DB: str = os.getenv('POSTGRES_DB','postgresql+asyncpg://postgres:postgres@postgres:5432/users_db')

    # SQLite (fallback if needed)
    SQLITE_DB_PATH: str = os.getenv('SQLITE_DB_PATH', 'db1.db')

    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'changeme-super-secret-key')

    # CORS
    RAW_CORS_ORIGINS: str = os.getenv('BACKEND_CORS_ORIGINS', '')
    BACKEND_CORS_ORIGINS: List[str] = parse_cors(RAW_CORS_ORIGINS)
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', '')
    
    @property
    def server_host(self) -> str:
        return f"http://{self.DOMAIN}" if self.ENVIRONMENT == "local" else f"https://{self.DOMAIN}"
    @property
    def google_service_account_info(self) -> dict:
        """
        Returns the parsed JSON content of the Google service account key,
        or raises an error if it's missing or invalid.
        """
        if not self.GOOGLE_SERVICE_ACCOUNT_JSON:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set")
        try:
            return json.loads(self.GOOGLE_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
    
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

    @property
    def ELASTIC_DATABASE_URI(self) -> str:
        if self.ENVIRONMENT in ["local"]:
            # return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"  # SQLite URI
            return self.ELASTIC_DB
        elif self.ENVIRONMENT in ["staging", "production"]:
            # for docker
            # return self.ELASTIC_DB

            # for render
            return self.ELASTIC_DB
        else:
            raise ValueError("Invalid ENVIRONMENT for database connection")

# Instantiate the settings object
settings = Settings()


