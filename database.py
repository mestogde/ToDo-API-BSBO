from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase  # базовый класс для моделей SQLAlchemy 2.0 (новый стиль)
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

try:
    from models.task import Task
    from models import Base
except ImportError:
    class Base(DeclarativeBase):
        pass

# Загрузка переменных окружения
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Создание асинхронного движка базы данных
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"statement_cache_size": 0}
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
    
    print("База данных инициализирована!")


async def drop_db():
    """
    Удаление всех таблиц из базы данных.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("Все таблицы удалены!")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения асинхронной сессии базы данных.
    
    Yields:
        AsyncSession: Асинхронная сессия для работы с БД
    """
    async with AsyncSessionLocal() as session:
        yield session