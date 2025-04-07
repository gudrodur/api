
# 📞 Secure Sales CRM API

A modern, modular CRM system built with **FastAPI**, JWT authentication, PostgreSQL backend, and comprehensive call/contact/sales tracking.

---

## 🚀 Features

- 🔐 **JWT OAuth2 authentication** with access and refresh tokens (assumes frontend AuthInterceptor)
- 🧠 **Async SQLAlchemy ORM** with PostgreSQL and Alembic migrations
- 📞 **Call logging** with auto-updated contact status based on disposition
- 📅 **Date filtering support** on call history using `from` and `to` query parameters
- 🧩 **Modular route design** (`users`, `contacts`, `calls`, `sales`, `statuses`)
- 🧪 **Unit tests with Pytest** and seed test data
- 🌍 **CORS, .env config, and FastAPI lifespan management**
- 📝 **Pydantic schemas** for input validation and OpenAPI documentation

---

## 🛠️ Setup Instructions

1. **Clone the repository:**
```bash
git clone https://github.com/gudrodur/api.git
cd api
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure your `.env` file (see example below)**

5. **Run the application:**
```bash
uvicorn sale_crm.main:app --reload
```

---

## 🧪 Testing

```bash
pytest
```

---

## 🔐 Example .env File

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sales_crm
SECRET_KEY=supersecretkey
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000
```

---

## 📂 Project Structure

```bash
api/
├── sale_crm/
│   ├── models/               # SQLAlchemy ORM models
│   ├── routes/               # API route modules
│   ├── auth.py               # JWT authentication & login
│   ├── db.py                 # Database configuration
│   ├── schemas.py            # Pydantic request/response models
│   ├── app_factory.py        # FastAPI app setup
│   ├── main.py               # Entry point with routing & CORS
│   └── test/                 # Unit tests
├── start                    # Startup script for powershell/bash
├── run.py                   # App entry point (legacy)
├── populate_database.py     # Seed test/demo data
├── setup_db.py              # Initialize database schema
├── requirements.txt
└── README.md
```

---

## 📚 Note

> All secured endpoints **require `AuthInterceptor`** in the frontend. It is assumed that the Authorization header is injected automatically in all API calls.

---

## 📬 Contact

> Project by `@gudrodur` – PRs and feedback welcome!
