from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from sale_crm.db import engine, Base
from sale_crm.routes import users, sales, calls
from sale_crm.auth import router as auth_router

# ==========================
# Lifespan Event Handler
# ==========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler to initialize the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("✅ Database initialized successfully!")
    yield  # Continue running the app

# ==========================
# Initialize FastAPI Application
# ==========================
app = FastAPI(
    title="Secure Sales CRM API",
    description="Sales CRM API with modular structure and authentication.",
    version="1.1.0",
    lifespan=lifespan  # ✅ Use the new lifespan event handler
)

# ==========================
# Configure Logging
# ==========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================
# Enable CORS for Frontend Access
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with allowed frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# Include API Routes
# ==========================
app.include_router(users.router)
app.include_router(sales.router)
app.include_router(calls.router)
app.include_router(auth_router)  # ✅ Register authentication routes

# ==========================
# API Health Check
# ==========================
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check route to verify if the API is running."""
    return {"status": "ok", "message": "API is running successfully!"}
