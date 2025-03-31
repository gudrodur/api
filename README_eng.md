## 🇬🇧 English Version

Welcome to the **Sales CRM** system! This is a secure, modular FastAPI REST API for managing phone sales, leads, users, calls, and statuses. Built with async SQLAlchemy and PostgreSQL, featuring JWT-based OAuth2 authentication.

---

### 🔐 Security

- Passwords hashed with **bcrypt**
- JWT access & refresh tokens with expiration
- Admin vs User access control

---

### 📁 Core Endpoints

- `/users` – Create, manage users
- `/contacts` – Contact management
- `/sales` – Sales tracking
- `/calls` – Log and fetch call records
- `/contact_status` – Status tagging for leads

---

### ⚙️ Environment Setup

Ensure `.env` is configured:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
SECRET_KEY=your-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Run locally:

```bash
uvicorn sale_crm.main:app --reload
```

Docs available at:
- Swagger: `/docs`
- ReDoc: `/redoc`

---

### ✍️ Author

Crafted for teams that need speed, flexibility, and security in a modern phone sales environment.