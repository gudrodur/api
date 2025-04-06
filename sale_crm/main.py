# main.py
from sale_crm.app_factory import app
from sale_crm.routes import contacts, users, sales, calls
from sale_crm.auth import router as auth_router

# ==========================
# ✅ Include API Routes
# ==========================
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(sales.router, prefix="/sales", tags=["sales"])
app.include_router(calls.router, prefix="/calls", tags=["calls"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])  # 👈 Mikilvægt!

# ==========================
# ✅ Health Check Route
# ==========================
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API is running successfully!"}
