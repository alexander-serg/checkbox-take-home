from typing import Any, Annotated

from pydantic import Field, HttpUrl, PositiveInt, UrlConstraints
from pydantic_settings import BaseSettings
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class Settings(BaseSettings):
    host_url: Annotated[HttpUrl, UrlConstraints(host_required=True)] = Field(default=...)
    host_port: PositiveInt = Field(default=...)

    auth_secret_key: str = Field(default=...)  # hint: openssl rand -hex 32
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 600

    database_host: str = Field(default=...)
    database_port: int = Field(default=...)
    database_user: str = Field(default=...)
    database_password: str = Field(default=...)
    database_name: str = Field(default=...)

    sqlalchemy_engine_options: dict[str, Any] = {
        'pool_size': 20,
        'pool_recycle': 600,
        'pool_pre_ping': True
    }


settings = Settings()


db_url = URL.create(
    drivername='postgresql+asyncpg',
    username=settings.database_user,
    password=settings.database_password,
    host=settings.database_host,
    port=settings.database_port,
    database=settings.database_name
)
db_engine = create_async_engine(db_url, **settings.sqlalchemy_engine_options)
async_session_factory = async_sessionmaker(bind=db_engine, expire_on_commit=False)
