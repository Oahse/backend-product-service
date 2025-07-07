import os
from typing import Any, List, Literal
from dotenv import load_dotenv

# Load environment variables from .env file located in the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env.production')
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

    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://default:4kZH1STNfGDscS29dCdbU7nJMPrDLZfh@redis-10990.c52.us-east-1-4.ec2.redns.redis-cloud.com:10990')

    # PostgreSQL
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_SERVER: str = os.getenv('POSTGRES_SERVER', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'users_db')

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
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.ENVIRONMENT in ["local"]:
            # return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"  # SQLite URI
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        elif self.ENVIRONMENT in ["staging", "production"]:
            # for docker
            # return 'postgresql+asyncpg://postgres:postgres@users-db:5432/users_db'

            # for render
            return 'postgresql+asyncpg://postgres:fAdvot-vyggeg-1rysku@db.htvauholjqlrfihihszd.supabase.co:5432/postgres'

            # return (
            #     f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            #     f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            # )
        else:
            raise ValueError("Invalid ENVIRONMENT for database connection")

# Instantiate the settings object
settings = Settings()


