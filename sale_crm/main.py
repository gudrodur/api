from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from sale_crm.db import engine, Base
from sale_crm.routes import contacts, users, sales, calls
from sale_crm.auth import router as auth_router
from dotenv import load_dotenv
load_dotenv()


# ==========================
# ✅ Load Environment Variables
# ==========================
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")  # ✅ Secure CORS
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ==========================
# ✅ Configure Logging
# ==========================
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# ==========================
# 🔥 Lifespan Event Handler (Avoid Unnecessary Table Creation)
# ==========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for database setup (Avoid `Base.metadata.create_all`)."""
    logger.info("🚀 API is starting up...")
    yield  # Continue running the app
    logger.info("🔄 API is shutting down...")

# ==========================
# ✅ Initialize FastAPI Application
# ==========================
app = FastAPI(
    title="Secure Sales CRM API",
    description="Sales CRM API with modular structure, authentication, and database management.",
    version="1.2.0",
    lifespan=lifespan,  # ✅ Use improved lifespan handler
    docs_url="/docs",  # ✅ Enable Swagger UI
    redoc_url="/redoc",  # ✅ Enable ReDoc
)

# ==========================
# 🔥 Enable CORS for Frontend Access (Restrict Allowed Origins)
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 🔥 Restrict CORS for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# ✅ Include API Routes
# ==========================
app.include_router(users.router)
app.include_router(sales.router)
app.include_router(calls.router)
app.include_router(auth_router)  # ✅ Register authentication routes
app.include_router(contacts.router)

# ==========================
# ✅ API Health Check
# ==========================
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check route to verify if the API is running."""
    return {"status": "ok", "message": "API is running successfully!"}
