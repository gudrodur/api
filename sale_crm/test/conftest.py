import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.future import select
from passlib.context import CryptContext

from sale_crm.main import app
from sale_crm.db import async_session_maker
from sale_crm.models import UserDB
from sale_crm.auth import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture(scope="function")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def db_session():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()  # tryggir hreint session
            await session.close()


@pytest.fixture(scope="function")
async def admin_token(db_session: AsyncSession) -> str:
    admin_user = await create_or_get_user(
        db_session,
        username="adminuser",
        email="admin@example.com",
        full_name="Admin",
        password="adminpass",
        role="admin"
    )
    return create_access_token(user_id=admin_user.id)


@pytest.fixture(scope="function")
async def test_user_token(db_session: AsyncSession) -> str:
    normal_user = await create_or_get_user(
        db_session,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="testpass",
        role="salesperson"
    )
    return create_access_token(user_id=normal_user.id)


async def create_or_get_user(session: AsyncSession, username: str, email: str, full_name: str, password: str, role: str):
    result = await session.execute(select(UserDB).where(UserDB.username == username))
    user = result.scalars().first()
    if user:
        return user

    new_user = UserDB(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=pwd_context.hash(password),
        role=role,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@pytest.fixture(autouse=True)
async def cleanup_tables():
    """Clean up database state between each test."""
    async with async_session_maker() as session:
        tables = [
            "calls",
            "sale_contacts",
            "sales",
            "sales_outcomes",
            "sale_status",
            "contact_list",
            "contact_status",
            "users"
        ]
        for table in tables:
            await session.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
        await session.commit()
