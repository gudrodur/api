# 📞 Secure Sales CRM API

Velkomin í **Sales CRM** kerfið! Þetta er öflugt og öruggt FastAPI REST API til að stjórna sölum, notendum, viðskiptavinum, símtölum og stöðustjórnun fyrir símasölu. Allt keyrt á PostgreSQL gagnagrunni með asyncronous SQLAlchemy ORM og JWT auðkenningu.

---

## 🚀 Yfirlit

- **API Rammi**: FastAPI + async SQLAlchemy
- **Gagnagrunnur**: PostgreSQL með Alembic fyrir migration
- **Auðkenning**: OAuth2 + JWT Tokens + Bcrypt fyrir lykilorð
- **Skráaruppbygging**: Modular með routes fyrir `users`, `contacts`, `sales`, `calls` og stöður
- **Frontend Testing**: Prófað með Android Studio (Samsung S23 Ultra)
- **Logging**: Miðlægt logging fyrir debugging og eftirlit
- **CORS**: Öruggt með stillanlegum leyfilegum uppruna

---

## 🔒 Öryggi

- Lykilorð eru hashuð með **bcrypt**
- JWT tokens með gildistíma fyrir bæði Access og Refresh
- Einungis admins hafa aðgang að viðkvæmum leiðum eins og `GET /users` eða `GET /sales`

---

## 📁 Helstu Routes

### 🧑‍💼 Notendur `/users`
- POST `/users` – Búa til nýjan notanda
- GET `/users` – Sækja alla (admin only)
- PUT/DELETE/GET `/users/{id}` – Sjálfur eða admin

### ☎️ Tengiliðir `/contacts`
- POST `/contacts` – Búa til tengilið
- GET `/contacts` – Sækja alla tengiliði
- PUT/DELETE/GET `/contacts/{id}` – Uppfæra, eyða, sækja
- GET `/contacts/contact/{id}` – Símtöl eftir tengilið

### 💼 Sala `/sales`
- POST `/sales` – Búa til sölu
- GET `/sales` – Sækja allar (admin only)
- PUT/DELETE/GET `/sales/{id}` – Sjálfur eða admin

### 📞 Símtöl `/calls`
- POST `/calls` – Skrá símtal
- GET `/calls` – Sjá eigin símtöl (admin sér öll)
- DELETE/GET `/calls/{id}` – Eyða/sækja

### 📊 Stöður
- `/contact_status` – CRUD á stöðum tengiliða
- `/sale_status`, `/sales_outcomes` – Notað í tengslum við sölu (ekki fullroutað)

---

## 🧬 Skema Samræmi

Samræmist `2025-03-31_phone_sales.pdf` með öllum dálkum, gagnategundum og tengslum við haldið í `models.py`.

---

## ⚙️ Keyrsla (Dev)

```bash
# .env þarf að innihalda:
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
SECRET_KEY=your-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=http://localhost:3000

# Keyra app
uvicorn sale_crm.main:app --reload
