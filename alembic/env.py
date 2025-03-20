import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sale_crm.models import Base  # ✅ Correct: Import models directly

# ==========================
# Load Database Configuration
# ==========================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:adminpass@localhost:5432/phone_sales")

# Load Alembic config file
config = context.config
fileConfig(config.config_file_name)

# ✅ Set target metadata for Alembic (ensures table detection)
target_metadata = Base.metadata


# ==========================
# Define Migration Function
# ==========================
def do_run_migrations(connection):
    """Run actual migrations."""
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode using an async engine."""
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations():
    """Main entrypoint for Alembic migrations."""
    if context.is_offline_mode():
        context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
    else:
        asyncio.run(run_migrations_online())
