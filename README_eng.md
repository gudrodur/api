# 📞 Secure Sales CRM API

A full-featured **Sales CRM system built with FastAPI**, using JWT-based authentication, PostgreSQL with async SQLAlchemy ORM, and modular routing for users, contacts, calls, and sales.

---

## 🚀 Features

- 🔐 JWT OAuth2 login (access + refresh tokens)
- 🧠 Async SQLAlchemy ORM with PostgreSQL backend
- 📞 Contact, Call, and Sale lifecycle management
- 🧩 Modular route structure (users, contacts, calls, sales)
- 🧪 Built-in testing with Pytest and demo data
- 🌍 CORS, environment config via `.env`, and lifecycle logging
- 📝 Pydantic validation schemas with full OpenAPI support

---

## 🛠️ Setup

1. **Clone the repo:**
```bash
git clone https://github.com/gudrodur/api.git
cd api
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Create your `.env` file (see below)**

5. **Run the API:**
```bash
uvicorn main:app --reload
```

---

## 🧪 Run Tests

```bash
pytest
```

---

## 🔐 .env Example

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sales_crm
SECRET_KEY=supersecretkey
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000
```

---

## 🗂️ Project Structure

```bash
api/
├── sale_crm/
│   ├── models/               # SQLAlchemy ORM models
│   ├── routes/               # FastAPI routes
│   ├── auth.py               # JWT & authentication logic
│   ├── db.py                 # Database engine and session
│   ├── schemas.py            # Pydantic models
│   ├── app_factory.py        # App factory with middleware
│   └── main.py               # Entrypoint to start API
├── populate_database.py      # Inserts demo/test data
├── requirements.txt
└── README.md
```

---

## 📬 Contact

> Created by `gudrodur` – PRs, issues, and feedback welcome!