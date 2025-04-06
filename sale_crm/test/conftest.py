import asyncio
import os
import platform
from typing import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from jose import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from sale_crm.app_factory import app
from sale_crm.db import SessionLocal
from sale_crm.models import UserDB, ContactList
from sale_crm.auth import hash_password

SECRET_KEY = "test-secret"
ALGORITHM = "HS256"

# ✅ Use SelectorEventLoopPolicy for Windows to avoid asyncio/socket errors
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an HTTPX async client bound to the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields an isolated DB session for each test."""
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user_token(db_session: AsyncSession) -> str:
    """Creates or resets a primary test user and returns a JWT token."""
    await db_session.execute(delete(UserDB).where(UserDB.email == "tester@example.com"))
    await db_session.commit()

    user = UserDB(
        username="tester",
        email="tester@example.com",
        full_name="Test User",
        hashed_password=hash_password("test123"),
        role="salesperson",
        phone="+3547770000",
        phone2=None
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return jwt.encode({"sub": str(user.id)}, SECRET_KEY, algorithm=ALGORITHM)


@pytest_asyncio.fixture
async def another_user_token(db_session: AsyncSession) -> str:
    """Creates or resets another test user and returns a JWT token."""
    await db_session.execute(delete(UserDB).where(UserDB.email == "another@example.com"))
    await db_session.commit()

    user = UserDB(
        username="another",
        email="another@example.com",
        full_name="Other User",
        hashed_password=hash_password("other123"),
        role="salesperson"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return jwt.encode({"sub": str(user.id)}, SECRET_KEY, algorithm=ALGORITHM)


@pytest_asyncio.fixture
async def test_contact_id(db_session: AsyncSession) -> int:
    """Creates a test contact and returns its ID."""
    # 🧹 Delete if already exists to avoid unique key error
    await db_session.execute(delete(ContactList).where(ContactList.phone == "+3548888888"))
    await db_session.commit()

    contact = ContactList(
        name="Test Contact",
        phone="+3548888888",
        status_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)
    return contact.id


@pytest.fixture(scope="session")
def anyio_backend():
    return 'asyncio'
