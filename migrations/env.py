import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://devmentor:devmentor_dev_password@postgres:5432/devmentor",
    )
    # Migrations run synchronously -- standardized on psycopg (v3)
    # explicitly, same driver persistence.py already requires, rather
    # than the implicit psycopg2 default and needing two sync drivers
    # installed everywhere.
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg://")


def run_migrations_offline():
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
