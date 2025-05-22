from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.adapters.api.payment_router import router as payment_router
from app.adapters.models.sql.base import Base
from app.adapters.models.sql.session import engine
from app.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Payments Service API",
    description="API for managing payment transactions and processing",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Payments Service Team",
        "url": "http://example.com/contact/",
        "email": "contact@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    payment_router,
    prefix=f"{settings.API_PREFIX}/payments",
    tags=["payments"],
)


@app.get("/", tags=["health"], summary="Health Check", description="Returns the health status of the service")
def health_check():
    """
    Performs a health check of the service.
    
    Returns:
        dict: A dictionary containing the service status and name
    """
    return {"status": "ok", "service": "payments-service"} 