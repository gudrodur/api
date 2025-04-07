from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 🔄 Load environment variables
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# 🔌 Import routers
from sale_crm.auth import router as auth_router
from sale_crm.routes.contact_status import router as contact_status_router
from sale_crm.routes.users import router as users_router
from sale_crm.routes.contacts import router as contacts_router
from sale_crm.routes.calls import router as calls_router
from sale_crm.routes.sales import router as sales_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 API is starting up...")
    yield
    logger.info("🔄 API is shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Secure Sales CRM API",
        description="Sales CRM with full JWT auth, contact/call/sale management.",
        version="1.2.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 🔗 Include all routers
    app.include_router(auth_router, prefix="/auth", tags=["Auth"])
    app.include_router(users_router, prefix="/users", tags=["Users"])
    app.include_router(contact_status_router, prefix="/contact_status", tags=["Contact Status"])
    app.include_router(contacts_router, prefix="/contacts", tags=["Contacts"])
    app.include_router(calls_router, prefix="/calls", tags=["Calls"])
    app.include_router(sales_router, prefix="/sales", tags=["Sales"])

    return app