
# 📞 Secure Sales CRM API

**Sales CRM kerfi byggt á FastAPI**, með JWT auðkenningu, PostgreSQL gagnagrunnstengingu, dagsetningarsíum og modular uppsetningu fyrir notendur, tengiliði, símtöl og sölustöður.

---

## 🚀 Eiginleikar

- 🔐 **JWT OAuth2 auðkenning** með `access` og `refresh` tokens (via `AuthInterceptor` í framenda)
- 🧠 **Async SQLAlchemy ORM** fyrir PostgreSQL með `AsyncSession` og Alembic
- 📞 **Símtalaskrá með sjálfvirkri tengiliðastöðu-uppfærslu** út frá `disposition`
- 📅 **Date filtering** fyrir símtalaleit með `from` og `to` query-parametrum
- 🧩 **Modular route uppbygging** (`users`, `contacts`, `calls`, `sales`, `statuses`)
- 🧪 **Pytest einingaprófanir** og `populate_database.py` fyrir testgögn
- 🌍 **CORS, .env stuðningur, líftímaviðföng (`lifespan`)**
- 📝 **Pydantic skemu** fyrir input validation og sjálfvirka OpenAPI skjölun

---

## 🛠️ Uppsetning

1. **Afritaðu verkefnið:**
```bash
git clone https://github.com/gudrodur/api.git
cd api
```

2. **Búðu til virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # á Windows: .\venv\Scripts\activate
```

3. **Settu upp pakkana:**
```bash
pip install -r requirements.txt
```

4. **Settu upp `.env` skrá (sjá dæmi neðar)**

5. **Ræstu appið með Uvicorn:**
```bash
uvicorn sale_crm.main:app --reload
```

---

## 🧪 Prófanir

```bash
pytest
```

---

## 🔐 .env skrá (dæmi)

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sales_crm
SECRET_KEY=supersecretkey
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000
```

---

## 📂 Verkefnistré

```bash
api/
├── sale_crm/
│   ├── models/               # SQLAlchemy ORM módel
│   ├── routes/               # API route modules
│   ├── auth.py               # Login, token handling, hashing
│   ├── db.py                 # Gagnagrunnstenging og session config
│   ├── schemas.py            # Pydantic input/output skemu
│   ├── app_factory.py        # FastAPI app setup og middleware
│   ├── main.py               # Tengir app, routers og CORS
│   └── test/                 # Pytest einingaprófanir
├── start                    # Ræsi-skrá fyrir powershell eða bash
├── run.py                   # Entry point (ef ekki notað `main`)
├── populate_database.py     # Fyllir test/demo gögn
├── setup_db.py              # Init gagnagrunns og töflur
├── requirements.txt
└── README.md
```

---

## 📚 Athugið

> Allar requests sem þurfa auðkenningu **treysta á virkt `AuthInterceptor`** í framenda. Tryggðu að Authorization haus sé settur sjálfvirkt í öllum köllum.

---

## 📬 Hafðu samband

> Verkefni eftir `@gudrodur` – velkomið að senda PR, athugasemdir eða skila hugmyndum!


### 🔄 Sorting Support on Call History

The following route now supports **optional sorting**:

```
GET /contacts/{id}/calls?from=...&to=...&sort_by=created_at&order=asc|desc
```

- `sort_by=created_at` (default) – Sort by creation time
- `order=desc` (default) – Newest first. Use `asc` for oldest first

**Example:**
```http
/calls/contacts/14/calls?from=2025-04-01&to=2025-04-07&order=asc
```
