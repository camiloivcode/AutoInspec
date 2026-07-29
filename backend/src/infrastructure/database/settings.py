from dataclasses import dataclass, field
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os


class Base(DeclarativeBase):
    pass


@dataclass
class DatabaseSettings:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "postgres"))
    database: str = field(default_factory=lambda: os.getenv("DB_NAME", "vehicular_inspections"))
    echo: bool = field(default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true")

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def url_sync(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


_engine = None
_session_factory = None


def get_engine(settings: Optional[DatabaseSettings] = None):
    global _engine
    if _engine is None:
        s = settings or DatabaseSettings()
        _engine = create_async_engine(s.url, echo=s.echo, pool_size=10, max_overflow=20)
    return _engine


def get_session_factory(settings: Optional[DatabaseSettings] = None):
    global _session_factory
    if _session_factory is None:
        engine = get_engine(settings)
        _session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _session_factory


async def create_tables():
    from .models import Base
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    from .models import Base
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
