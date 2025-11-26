from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

class Base(DeclarativeBase):
    pass

DATABASE_URL = os.getenv("DATABASE_URL")

# Создание асинхронного движка базы данных с отключением кэширования prepared statements
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "statement_cache_size": 0,  # Отключаем кэш prepared statements
        "prepared_statement_name_func": lambda: f"stmt_{uuid.uuid4().hex}"  # Уникальные имена для statements
    }
)

# Создание фабрики асинхронных сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


async def init_db():
    """
    Инициализация базы данных - создание всех таблиц.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ База данных инициализирована!")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения асинхронной сессии базы данных.
    
    Yields:
        AsyncSession: Асинхронная сессия для работы с БД
    """
    async with AsyncSessionLocal() as session:
        yield session