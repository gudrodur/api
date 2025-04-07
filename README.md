# 📞 Secure Sales CRM API

**Sales CRM kerfi byggt á FastAPI** með JWT auðkenningu, PostgreSQL gagnagrunnstengingu, og modular uppsetningu fyrir notendur, viðskiptavini, símtöl og sölu.

---

## 🚀 Eiginleikar

- 🔐 JWT OAuth2 auðkenning (access og refresh tokens)
- 🧠 Async SQLAlchemy ORM fyrir PostgreSQL
- 📞 Viðskiptavinir, símtöl og söluferli með stöðuyfirliti
- 🧩 Modular router uppbygging (users, contacts, calls, sales)
- 🧪 Pytest testkerfi og prófunargögn
- 🌍 CORS, .env stuðningur, og líftíma-stýring
- 📝 Pydantic skemu fyrir validation og OpenAPI

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
source venv/bin/activate  # eða .\venv\Scripts\activate á Windows
```

3. **Settu upp pakkana:**
```bash
pip install -r requirements.txt
```

4. **Settu upp .env skrá (sjá dæmi neðar)**

5. **Keyrðu verkefnið:**
```bash
uvicorn main:app --reload
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

## 🗂️ Verkefnistré

```bash
api/
├── sale_crm/
│   ├── models/               # SQLAlchemy ORM módel
│   ├── routes/               # API endpointar
│   ├── auth.py               # JWT & login
│   ├── db.py                 # DB tengingar
│   ├── schemas.py            # Pydantic skemu
│   ├── app_factory.py        # Býr til app
│   └── main.py               # Ræsir appið
├── populate_database.py      # Test gögn
├── requirements.txt
└── README.md
```

---

## 📬 Hafðu samband

> Unnið af `gudrodur` – velkomið að senda PR, athugasemdir eða skila hugmyndum!