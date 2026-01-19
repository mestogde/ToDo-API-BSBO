# main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import init_db, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from routers import tasks, stats, auth, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Запуск приложения...")
    # Для Supabase не вызываем init_db() - таблицы уже созданы через SQL
    print("✅ Приложение готово к работе!")
    yield
    print("🛑 Остановка приложения...")


app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Подключение роутеров - ВЕРСИЯ 3.0
app.include_router(auth.router, prefix="/api/v3", tags=["auth"])
app.include_router(tasks.router, prefix="/api/v3", tags=["tasks"])
app.include_router(stats.router, prefix="/api/v3", tags=["stats"])
app.include_router(admin.router, prefix="/api/v3", tags=["admin"])

# Подключение статических файлов для фронтенда
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
async def read_root() -> dict:
    return {
        "message": "Task Manager API - Управление задачами по матрице Эйзенхауэра",
        "version": "3.0.0",
        "database": "PostgreSQL (Supabase)",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_async_session)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {"status": "healthy", "database": db_status}