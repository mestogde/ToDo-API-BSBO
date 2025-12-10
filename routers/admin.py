# routers/admin.py
from sqlalchemy import case
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_async_session
from models import User, Task
from dependencies import get_current_admin
from typing import List, Dict, Any

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def get_all_users(
    db: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)
):
    """
    Получение списка всех пользователей с количеством задач
    
    Только для администраторов
    """
    # Получаем всех пользователей с подсчетом их задач
    result = await db.execute(
        select(
            User.id,
            User.nickname,
            User.email,
            User.role,
            func.count(Task.id).label("task_count")
        )
        .outerjoin(Task, User.id == Task.user_id)
        .group_by(User.id)
        .order_by(User.id)
    )
    
    users = result.all()
    
    return [
        {
            "id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "role": user.role,
            "task_count": user.task_count
        }
        for user in users
    ]


@router.get("/users/{user_id}/tasks")
async def get_user_tasks(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)
):
    """
    Получение всех задач конкретного пользователя
    
    Только для администраторов
    """
    # Проверяем существование пользователя
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем задачи пользователя
    tasks_result = await db.execute(
        select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
    )
    tasks = tasks_result.scalars().all()
    
    return {
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "email": user.email,
            "role": user.role
        },
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "quadrant": task.quadrant,
                "completed": task.completed,
                "created_at": task.created_at,
                "deadline_at": task.deadline_at
            }
            for task in tasks
        ]
    }


@router.get("/stats/overview")
async def get_admin_stats(
    db: AsyncSession = Depends(get_async_session),
    admin: User = Depends(get_current_admin)
):
    """
    Расширенная статистика для администратора
    
    Только для администраторов
    """
    # Общая статистика по пользователям
    users_result = await db.execute(
        select(
            func.count(User.id).label("total_users"),
            func.sum(case((User.role == "admin", 1), else_=0)).label("admin_count")
        )
    )
    users_stats = users_result.first()
    
    # Общая статистика по задачам
    tasks_result = await db.execute(
        select(
            func.count(Task.id).label("total_tasks"),
            func.sum(case((Task.completed == True, 1), else_=0)).label("completed_tasks"),
            func.sum(case((Task.deadline_at.isnot(None), 1), else_=0)).label("tasks_with_deadline")
        )
    )
    tasks_stats = tasks_result.first()
    
    # Статистика по квадрантам
    quadrant_result = await db.execute(
        select(Task.quadrant, func.count(Task.id))
        .group_by(Task.quadrant)
    )
    quadrant_stats = dict(quadrant_result.all())
    
    # Задачи по пользователям (топ 10)
    users_tasks_result = await db.execute(
        select(
            User.nickname,
            func.count(Task.id).label("task_count")
        )
        .outerjoin(Task, User.id == Task.user_id)
        .group_by(User.id)
        .order_by(func.count(Task.id).desc())
        .limit(10)
    )
    top_users = users_tasks_result.all()
    
    return {
        "users": {
            "total": users_stats.total_users or 0,
            "admins": users_stats.admin_count or 0,
            "regular": (users_stats.total_users or 0) - (users_stats.admin_count or 0)
        },
        "tasks": {
            "total": tasks_stats.total_tasks or 0,
            "completed": tasks_stats.completed_tasks or 0,
            "with_deadline": tasks_stats.tasks_with_deadline or 0,
            "completion_rate": round((tasks_stats.completed_tasks / tasks_stats.total_tasks * 100) if tasks_stats.total_tasks else 0, 1),
            "by_quadrant": quadrant_stats
        },
        "top_users": [
            {"nickname": user.nickname, "task_count": user.task_count}
            for user in top_users
        ]
    }