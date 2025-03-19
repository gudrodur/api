import asyncio
import sys
import os
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.engine import Connection
from sqlalchemy import pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from alembic import context

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from setup_db import Base, DATABASE_URL  # Ensure correct import

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

engine = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

async def run_migrations_online():
    """Run migrations using async connection."""
    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)

def do_run_migrations(connection: Connection):
    """Helper function to run migrations synchronously."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_offline():
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
