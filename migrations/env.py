import sys
from os.path import dirname, abspath
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Добавляем путь, чтобы Python видел папку app
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from app.core.config import settings
from app.models.base import Base
from app.models.users import User 
from app.models.auth import Role, BusinessElement, AccessRule

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online() -> None:
    sync_url = settings.DATABASE_URL.replace("asyncpg", "psycopg2")
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = sync_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    url = settings.DATABASE_URL.replace("asyncpg", "psycopg2")
    context.configure(url=url, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()