import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base
# Ensure all models are imported for Alembic autogenerate
from app.models.user import User
from app.models.profile import Profile
from app.models.bid import Bid
from app.models.token_blacklist import TokenBlacklist
from app.models.autobid_log import AutobidLog
from app.models.autobid_settings import AutobidSettings
from app.models.ai_prompt import AIPrompt
from app.models.job import Job
# from app import models # Original import, can be kept or removed if explicit imports cover all
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ ВАЖНО
target_metadata = Base.metadata # All models should be registered with Base.metadata by now

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
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


# from app.models import autobid_settings # This specific import seems out of place here
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
