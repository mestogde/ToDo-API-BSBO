from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime, time
from models import Task
from database import get_async_session

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/")
async def get_tasks_stats(db: AsyncSession = Depends(get_async_session)):
    """
    Получение статистики по задачам
    
    Возвращает:
    - Общее количество задач
    - Количество задач по квадрантам
    - Количество выполненных и невыполненных задач
    """
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    
    total_tasks = len(tasks)
    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    by_status = {"completed": 0, "pending": 0}
    
    for task in tasks:
        if task.quadrant in by_quadrant:
            by_quadrant[task.quadrant] += 1
        if task.completed:
            by_status["completed"] += 1
        else:
            by_status["pending"] += 1
    
    return {
        "total_tasks": total_tasks,
        "by_quadrant": by_quadrant,
        "by_status": by_status
    }


@router.get("/deadlines")
async def get_deadlines_stats(db: AsyncSession = Depends(get_async_session)):
    """Статистика по дедлайнам для невыполненных задач"""
    result = await db.execute(
        select(Task).where(Task.completed == False)
    )
    tasks = result.scalars().all()
    
    today = date.today()
    deadline_stats = []
    overdue_tasks = 0
    
    for task in tasks:
        if task.deadline_at:
            deadline_date = task.deadline_at.date()
            days_until_deadline = (deadline_date - today).days
            
            # Определяем статус дедлайна
            if days_until_deadline < 0:
                status = "overdue"
                overdue_tasks += 1
            elif days_until_deadline <= 3:
                status = "urgent"
            else:
                status = "normal"
            
            deadline_stats.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "created_at": task.created_at,
                "deadline_at": task.deadline_at,
                "days_until_deadline": days_until_deadline,
                "status": status,
                "is_urgent": days_until_deadline <= 3,
                "quadrant": task.quadrant
            })
    
    # Сортируем: просроченные → срочные → обычные
    deadline_stats.sort(key=lambda x: x["days_until_deadline"])
    
    urgent_tasks = len([t for t in deadline_stats if t["is_urgent"] and t["status"] != "overdue"])
    
    return {
        "total_pending_with_deadlines": len(deadline_stats),
        "overdue_tasks": overdue_tasks,
        "urgent_tasks": urgent_tasks,
        "normal_tasks": len(deadline_stats) - overdue_tasks - urgent_tasks,
        "tasks": deadline_stats
    }


@router.get("/today")
async def get_today_stats(db: AsyncSession = Depends(get_async_session)):
    """
    Статистика по задачам на сегодня
    
    Возвращает:
    - Общее количество задач на сегодня
    - Распределение по квадрантам
    - Статус выполнения
    """
    # Получаем сегодняшнюю дату
    today = date.today()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    # Ищем задачи с дедлайном на сегодня
    result = await db.execute(
        select(Task).where(
            Task.deadline_at.between(today_start, today_end)
        )
    )
    tasks = result.scalars().all()
    
    total_tasks_today = len(tasks)
    
    # Статистика по квадрантам
    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    
    # Статистика по статусу выполнения
    by_status = {"completed": 0, "pending": 0}
    
    # Список задач для детального отчета
    today_tasks = []
    
    for task in tasks:
        # Подсчет по квадрантам
        if task.quadrant in by_quadrant:
            by_quadrant[task.quadrant] += 1
        
        # Подсчет по статусам
        if task.completed:
            by_status["completed"] += 1
        else:
            by_status["pending"] += 1
        
        # Добавляем задачу в детальный отчет
        today_tasks.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "is_important": task.is_important,
            "quadrant": task.quadrant,
            "completed": task.completed,
            "deadline_at": task.deadline_at,
            "created_at": task.created_at
        })
    
    return {
        "date": today.isoformat(),
        "total_tasks_due_today": total_tasks_today,
        "by_quadrant": by_quadrant,
        "by_status": by_status,
        "completion_rate": round((by_status["completed"] / total_tasks_today * 100) if total_tasks_today > 0 else 0, 1),
        "tasks": today_tasks
    }