import sys
import os
from logging.config import fileConfig

from sqlalchemy import create_engine
from alembic import context
from src.db.session import Base
from src.core.config import settings

# Tambahkan direktori proyek ke PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Import semua model di sini
from src.models.category_model import Category
from src.models.radiograph_model import Radiograph
from src.models.user_model import User

# Konfigurasi logging
if context.config.config_file_name:
    fileConfig(context.config.config_file_name)

# Tentukan metadata dari model-model
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_engine(settings.DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
