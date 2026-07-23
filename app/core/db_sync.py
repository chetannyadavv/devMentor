from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Celery tasks are naturally synchronous -- same reasoning as Alembic
# using a sync connection while the app itself runs async.
_sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
sync_engine = create_engine(_sync_url)
SyncSessionLocal = sessionmaker(bind=sync_engine)
