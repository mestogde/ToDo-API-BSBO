from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from routers import tasks

app = FastAPI(
    title="ToDo лист API",
    description="API для управления задачами с использованием матрицы Эйзенхауэра",
    version="1.0.0",
    contact={"name": "Ксения"}
)

# Модель Pydantic для создания новой задачи
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    is_important: bool
    is_urgent: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Новая задача",
                "description": "Описание новой задачи",
                "is_important": True,
                "is_urgent": False
            }
        }

# Модель Pydantic для ответа (включает все поля)
class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    is_important: bool
    is_urgent: bool
    quadrant: str
    completed: bool
    created_at: datetime

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


# Простой POST запрос для создания новой задачи
@app.post("/tasks/create", response_model=TaskResponse, tags=["tasks"])
async def create_task(task_data: TaskCreate):
    """
    Создание новой задачи с валидацией данных
    
    - **title**: Название задачи (обязательное)
    - **description**: Описание задачи (опциональное)
    - **is_important**: Важная ли задача
    - **is_urgent**: Срочная ли задача
    """
    
    # Определяем квадрант на основе важности и срочности
    if task_data.is_important and task_data.is_urgent:
        quadrant = "Q1"
    elif task_data.is_important and not task_data.is_urgent:
        quadrant = "Q2"
    elif not task_data.is_important and task_data.is_urgent:
        quadrant = "Q3"
    else:
        quadrant = "Q4"
    
    # Создаем новую задачу
    new_task = {
        "id": len(tasks.tasks_db) + 1,
        "title": task_data.title,
        "description": task_data.description,
        "is_important": task_data.is_important,
        "is_urgent": task_data.is_urgent,
        "quadrant": quadrant,
        "completed": False,
        "created_at": datetime.now()
    }
    
    # Добавляем задачу в базу данных
    tasks.tasks_db.append(new_task)
    
    return new_task


# Дополнительный POST для отметки задачи как выполненной
@app.post("/tasks/{task_id}/complete", tags=["tasks"])
async def complete_task(task_id: int):
    """
    Отметить задачу как выполненную
    
    - **task_id**: ID задачи для отметки как выполненной
    """
    for task in tasks.tasks_db:
        if task["id"] == task_id:
            task["completed"] = True
            return {
                "message": f"Задача '{task['title']}' отмечена как выполненная",
                "task_id": task_id,
                "completed": True
            }
    
    raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")