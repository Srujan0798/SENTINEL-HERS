"""Alembic env — uses DATABASE_URL from environment, imports all ORM models."""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path so we can import src.backend models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from DATABASE_URL env var
db_url = os.getenv("DATABASE_URL", "")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Import all models so autogenerate knows about them
import src.backend.shared_models  # noqa
from src.backend.logs import models as _lm  # noqa
from src.backend.incidents import models as _im  # noqa
from src.backend.tasks import models as _tm  # noqa
from src.backend.comms import models as _cm  # noqa
from src.backend.integrations.github import models as _gm  # noqa

from src.backend.db import Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()