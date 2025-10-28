from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()

# временное хранилище
tasks_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Сдать проект по FastAPI",
        "description": "Завершить разработку API и написать документацию",
        "is_important": True,
        "is_urgent": True,
        "quadrant": "Q1",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 2,
        "title": "Изучить SQLAlchemy",
        "description": "Прочитать документацию и попробовать примеры",
        "is_important": True,
        "is_urgent": False,
        "quadrant": "Q2",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 3,
        "title": "Сходить на лекцию",
        "description": None,
        "is_important": False,
        "is_urgent": True,
        "quadrant": "Q3",
        "completed": False,
        "created_at": datetime.now()
    },
    {
        "id": 4,
        "title": "Посмотреть сериал",
        "description": "Новый сезон любимого сериала",
        "is_important": False,
        "is_urgent": False,
        "quadrant": "Q4",
        "completed": True,
        "created_at": datetime.now()
    },
]


@router.get("/")
async def get_all_tasks() -> dict:
    return {
        "count": len(tasks_db),
        "tasks": tasks_db
    }


@router.get("/stats")
async def get_tasks_stats() -> dict:
    total_tasks = len(tasks_db)
    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for task in tasks_db:
        q = task["quadrant"]
        if q in by_quadrant:
            by_quadrant[q] += 1

    completed = sum(1 for t in tasks_db if t["completed"])
    pending = total_tasks - completed

    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": {
            "completed": completed,
            "pending": pending
        }
    }


@router.get("/search")
async def search_tasks(q: str = Query(..., min_length=2)) -> dict:
    keyword = q.lower()
    results = [
        task for task in tasks_db
        if keyword in task["title"].lower()
        or (task["description"] and keyword in task["description"].lower())
    ]

    if not results:
        raise HTTPException(status_code=404, detail=f"Задачи, содержащие '{q}', не найдены")

    return {
        "query": q,
        "count": len(results),
        "tasks": results
    }


@router.get("/status/{status}")
async def get_tasks_by_status(status: str) -> dict:
    valid_statuses = ["completed", "pending"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=404, 
            detail=f"Статус '{status}' не найден. Допустимые статусы: {valid_statuses}"
        )
    
    # Преобразуем строковый статус в булево значение
    is_completed = status == "completed"
    
    filtered_tasks = [task for task in tasks_db if task["completed"] == is_completed]
    
    return {
        "status": status,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@router.get("/quadrant/{quadrant}")
async def get_tasks_by_quadrant(quadrant: str) -> dict:
    valid_quadrants = ["Q1", "Q2", "Q3", "Q4"]
    if quadrant not in valid_quadrants:
        raise HTTPException(
            status_code=404, 
            detail=f"Квадрант '{quadrant}' не найден. Допустимые квадранты: {valid_quadrants}"
        )
    
    filtered_tasks = [task for task in tasks_db if task["quadrant"] == quadrant]
    
    return {
        "quadrant": quadrant,
        "count": len(filtered_tasks),
        "tasks": filtered_tasks
    }


@router.get("/{task_id}")
async def get_task_by_id(task_id: int) -> dict:
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Задача с ID {task_id} не найдена")