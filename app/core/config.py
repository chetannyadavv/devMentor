from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://devmentor:devmentor_dev_password@localhost:5432/devmentor"
    # Dev-only default -- override via env var in any real deployment.
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    celery_broker_url: str = "redis://redis:6379/0"

    class Config:
        env_prefix = ""
        # Reads DATABASE_URL from the environment (case-insensitive match
        # to database_url), same variable name docker-compose sets for
        # the api container.


settings = Settings()
