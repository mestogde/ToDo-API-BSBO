from fastapi import FastAPI
from routers import tasks

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="1.0.0",
    contact={"name": "Ксения"}
)

# Включаем роутер задач с префиксом /tasks
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])


@app.get("/")
async def welcome() -> dict:
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version,
        "contact": app.contact,
    }