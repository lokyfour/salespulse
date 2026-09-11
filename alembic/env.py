"""
alembic/env.py

Alembic migration environment for salespulse.

Reads DATABASE_URL from environment (set in .env or docker-compose).
Imports all ORM models so autogenerate detects schema changes.

Usage:
    # Apply all pending migrations
    alembic upgrade head

    # Generate a new migration from model changes
    alembic revision --autogenerate -m "describe change"

    # Roll back one migration
    alembic downgrade -1
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Import all models so autogenerate can see them ──────────────────────
# Every new model file added to src/salespulse/models/ must be imported here.
from salespulse.models.call import Base  # noqa: F401 — imports Base
from salespulse.models.transcript import Transcript, Turn  # noqa: F401
from salespulse.models.scorecard import Scorecard, CriterionScore  # noqa: F401
from salespulse.models.rep import Rep  # noqa: F401
from salespulse.models.coaching import CoachingReport  # noqa: F401

# ── Alembic config ───────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with DATABASE_URL from environment.
# This avoids storing the connection string in alembic.ini.
database_url = os.environ.get("DATABASE_URL", "")
if database_url.startswith("postgresql+asyncpg://"):
    # Alembic uses a sync driver; strip the asyncpg dialect for migrations.
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL only)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live PostgreSQL connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # Detect column type changes
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
