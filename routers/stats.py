# routers/stats.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, time
from models import Task, User
from database import get_async_session
from dependencies import get_current_user

router = APIRouter(tags=["statistics"])


@router.get("/")
async def get_tasks_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Получение статистики по задачам
    """
    print(f"DEBUG: stats.py - get_tasks_stats вызван, пользователь: {current_user}")
    
    if current_user.role == "admin":
        # Администратор видит статистику по всем задачам
        total_result = await db.execute(select(func.count(Task.id)))
        total_tasks = total_result.scalar()
        
        quadrant_result = await db.execute(
            select(Task.quadrant, func.count(Task.id))
            .group_by(Task.quadrant)
        )
        by_quadrant = dict(quadrant_result.all())
        
        status_result = await db.execute(
            select(Task.completed, func.count(Task.id))
            .group_by(Task.completed)
        )
        status_data = dict(status_result.all())
    else:
        # Обычный пользователь видит статистику только по своим задачам
        total_result = await db.execute(
            select(func.count(Task.id)).where(Task.user_id == current_user.id)
        )
        total_tasks = total_result.scalar()
        
        quadrant_result = await db.execute(
            select(Task.quadrant, func.count(Task.id))
            .where(Task.user_id == current_user.id)
            .group_by(Task.quadrant)
        )
        by_quadrant = dict(quadrant_result.all())
        
        status_result = await db.execute(
            select(Task.completed, func.count(Task.id))
            .where(Task.user_id == current_user.id)
            .group_by(Task.completed)
        )
        status_data = dict(status_result.all())
    
    # Форматируем результат
    by_status = {"completed": status_data.get(True, 0), "pending": status_data.get(False, 0)}
    
    # Заполняем все квадранты нулями если их нет
    all_quadrants = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    all_quadrants.update(by_quadrant)
    
    return {
        "total_tasks": total_tasks,
        "by_quadrant": all_quadrants,
        "by_status": by_status
    }


@router.get("/deadlines")
async def get_deadlines_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Статистика по дедлайнам для невыполненных задач"""
    print(f"DEBUG: stats.py - get_deadlines_stats вызван, пользователь: {current_user}")
    
    if current_user.role == "admin":
        result = await db.execute(
            select(Task).where(Task.completed == False)
        )
    else:
        result = await db.execute(
            select(Task).where(
                Task.completed == False,
                Task.user_id == current_user.id
            )
        )
    
    tasks = result.scalars().all()
    
    today = date.today()
    deadline_stats = []
    overdue_tasks = 0
    
    for task in tasks:
        if task.deadline_at:
            deadline_date = task.deadline_at.date()
            days_until_deadline = (deadline_date - today).days
            
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
                "quadrant": task.quadrant,
                "user_id": task.user_id
            })
    
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
async def get_today_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Статистика по задачам на сегодня
    """
    print(f"DEBUG: stats.py - get_today_stats вызван, пользователь: {current_user}")
    
    today = date.today()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    if current_user.role == "admin":
        result = await db.execute(
            select(Task).where(
                Task.deadline_at.between(today_start, today_end)
            )
        )
    else:
        result = await db.execute(
            select(Task).where(
                Task.deadline_at.between(today_start, today_end),
                Task.user_id == current_user.id
            )
        )
    
    tasks = result.scalars().all()
    
    total_tasks_today = len(tasks)
    
    by_quadrant = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    by_status = {"completed": 0, "pending": 0}
    today_tasks = []
    
    for task in tasks:
        if task.quadrant in by_quadrant:
            by_quadrant[task.quadrant] += 1
        
        if task.completed:
            by_status["completed"] += 1
        else:
            by_status["pending"] += 1
        
        today_tasks.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "is_important": task.is_important,
            "quadrant": task.quadrant,
            "completed": task.completed,
            "deadline_at": task.deadline_at,
            "created_at": task.created_at,
            "user_id": task.user_id
        })
    
    completion_rate = round((by_status["completed"] / total_tasks_today * 100) if total_tasks_today > 0 else 0, 1)
    
    return {
        "date": today.isoformat(),
        "total_tasks_due_today": total_tasks_today,
        "by_quadrant": by_quadrant,
        "by_status": by_status,
        "completion_rate": completion_rate,
        "tasks": today_tasks
    }