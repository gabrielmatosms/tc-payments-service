import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # SQL Database settings
    SQL_DATABASE_URL: str = os.getenv("SQL_DATABASE_URL", "sqlite:///./payments_service.db")
    
    # NoSQL Database settings (MongoDB)
    NOSQL_HOST: str = os.getenv("NOSQL_HOST", "localhost")
    NOSQL_PORT: int = int(os.getenv("NOSQL_PORT", "27017"))
    NOSQL_DB: str = os.getenv("NOSQL_DB", "payments_service")
    
    # API settings
    API_PREFIX: str = "/api/v1"
    
    # External services
    ORDERS_SERVICE_URL: str = os.getenv("ORDERS_SERVICE_URL", "http://localhost:8003")


settings = Settings() 