from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from models import Task
from database import get_async_session

router = APIRouter(prefix="/stats", tags=["statistics"])


@router.get("/")
async def get_tasks_stats(db: AsyncSession = Depends(get_async_session)):
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
        select(Task).where(Task.completed == False).where(Task.deadline_at.isnot(None))
    )
    tasks = result.scalars().all()
    
    today = date.today()
    deadline_stats = []
    
    for task in tasks:
        deadline_date = task.deadline_at.date()
        days_until_deadline = (deadline_date - today).days
        
        deadline_stats.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "created_at": task.created_at,
            "deadline_at": task.deadline_at,
            "days_until_deadline": days_until_deadline,
            "is_urgent": days_until_deadline <= 3,
            "quadrant": task.quadrant
        })
    
    # Сортируем по оставшемуся времени (сначала самые срочные)
    deadline_stats.sort(key=lambda x: x["days_until_deadline"])
    
    return {
        "total_pending_with_deadlines": len(deadline_stats),
        "urgent_tasks": len([t for t in deadline_stats if t["is_urgent"]]),
        "tasks": deadline_stats
    }