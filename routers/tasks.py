# routers/tasks.py
from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date, time

from database import get_async_session
from models.task import Task
from models.user import User
from schemas import TaskCreate, TaskResponse, TaskUpdate
from dependencies import get_current_user

router = APIRouter()


def calculate_urgency_and_quadrant(deadline_at: Optional[datetime], is_important: bool) -> tuple[bool, str]:
    """Рассчитывает срочность и квадрант на основе дедлайна и важности"""
    if not deadline_at:
        is_urgent = False
    else:
        today = date.today()
        deadline_date = deadline_at.date()
        
        if deadline_date < today:
            is_urgent = True
        else:
            days_until_deadline = (deadline_date - today).days
            is_urgent = days_until_deadline <= 3
    
    if is_important and is_urgent:
        quadrant = "Q1"
    elif is_important and not is_urgent:
        quadrant = "Q2"
    elif not is_important and is_urgent:
        quadrant = "Q3"
    else:
        quadrant = "Q4"
    
    return is_urgent, quadrant


def calculate_days_until_deadline(deadline_at: Optional[datetime]) -> Optional[int]:
    """Рассчитывает количество дней до дедлайна с учетом просрочки"""
    if not deadline_at:
        return None
    
    today = date.today()
    deadline_date = deadline_at.date()
    
    return (deadline_date - today).days


@router.get("/", response_model=List[TaskResponse])
async def get_all_tasks(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    """
    Получение всех задач
    
    Администратор видит все задачи, обычный пользователь - только свои
    """
    print(f"DEBUG: get_all_tasks вызван, пользователь: {current_user}")
    
    # Исправлено: убрали .value
    if current_user.role == "admin":
        result = await db.execute(select(Task))
    else:
        # Пользователь видит только свои задачи
        result = await db.execute(
            select(Task).where(Task.user_id == current_user.id)
        )
    
    tasks = result.scalars().all()
    
    response_tasks = []
    for task in tasks:
        is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        task_dict = {
            **task.__dict__,
            "is_urgent": is_urgent,
            "days_until_deadline": days_until_deadline
        }
        response_tasks.append(TaskResponse(**task_dict))
    
    return response_tasks


@router.get("/search", response_model=List[TaskResponse])
async def search_tasks(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    """
    Поиск задач по ключевому слову
    """
    keyword = f"%{q.lower()}%"
    
    # Исправлено: убрали .value
    if current_user.role == "admin":
        result = await db.execute(
            select(Task).where(
                (Task.title.ilike(keyword)) |
                (Task.description.ilike(keyword))
            )
        )
    else:
        result = await db.execute(
            select(Task).where(
                Task.user_id == current_user.id,
                (Task.title.ilike(keyword)) |
                (Task.description.ilike(keyword))
            )
        )
    
    tasks = result.scalars().all()
    
    if not tasks:
        raise HTTPException(
            status_code=404, 
            detail="По данному запросу ничего не найдено"
        )
    
    response_tasks = []
    for task in tasks:
        is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        task_dict = {
            **task.__dict__,
            "is_urgent": is_urgent,
            "days_until_deadline": days_until_deadline
        }
        response_tasks.append(TaskResponse(**task_dict))
    
    return response_tasks


@router.get("/status/{status}", response_model=List[TaskResponse])
async def get_tasks_by_status(
    status: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    """
    Фильтрация задач по статусу выполнения
    """
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=400, 
            detail="Недопустимый статус. Используйте: completed или pending"
        )
    
    is_completed = (status == "completed")
    
    # Исправлено: убрали .value
    if current_user.role == "admin":
        result = await db.execute(
            select(Task).where(Task.completed == is_completed)
        )
    else:
        result = await db.execute(
            select(Task).where(
                Task.completed == is_completed,
                Task.user_id == current_user.id
            )
        )
    
    tasks = result.scalars().all()
    
    response_tasks = []
    for task in tasks:
        is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        task_dict = {
            **task.__dict__,
            "is_urgent": is_urgent,
            "days_until_deadline": days_until_deadline
        }
        response_tasks.append(TaskResponse(**task_dict))
    
    return response_tasks


@router.get("/quadrant/{quadrant}", response_model=List[TaskResponse])
async def get_tasks_by_quadrant(
    quadrant: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    """
    Фильтрация задач по квадранту
    """
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4"
        )
    
    # Исправлено: убрали .value
    if current_user.role == "admin":
        result = await db.execute(
            select(Task).where(Task.quadrant == quadrant)
        )
    else:
        result = await db.execute(
            select(Task).where(
                Task.quadrant == quadrant,
                Task.user_id == current_user.id
            )
        )
    
    tasks = result.scalars().all()
    
    response_tasks = []
    for task in tasks:
        is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        task_dict = {
            **task.__dict__,
            "is_urgent": is_urgent,
            "days_until_deadline": days_until_deadline
        }
        response_tasks.append(TaskResponse(**task_dict))
    
    return response_tasks


@router.get("/today", response_model=List[TaskResponse])
async def get_tasks_due_today(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> List[TaskResponse]:
    """
    Получение задач, срок которых истекает сегодня
    """
    today = date.today()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    # Исправлено: убрали .value
    if current_user.role == "admin":
        result = await db.execute(
            select(Task).where(
                Task.deadline_at.between(today_start, today_end),
                Task.completed == False
            )
        )
    else:
        result = await db.execute(
            select(Task).where(
                Task.deadline_at.between(today_start, today_end),
                Task.completed == False,
                Task.user_id == current_user.id
            )
        )
    
    tasks = result.scalars().all()
    
    response_tasks = []
    for task in tasks:
        is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
        days_until_deadline = calculate_days_until_deadline(task.deadline_at)
        
        task_dict = {
            **task.__dict__,
            "is_urgent": is_urgent,
            "days_until_deadline": days_until_deadline
        }
        response_tasks.append(TaskResponse(**task_dict))
    
    return response_tasks


@router.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Получение задачи по ID
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Проверка прав доступа - исправлено: убрали .value
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой задаче"
        )
    
    is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    task_dict = {
        **task.__dict__,
        "is_urgent": is_urgent,
        "days_until_deadline": days_until_deadline
    }
    
    return TaskResponse(**task_dict)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Создание новой задачи
    """
    is_urgent, quadrant = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
    
    new_task = Task(
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        deadline_at=task.deadline_at,
        quadrant=quadrant,
        completed=False,
        user_id=current_user.id  # Привязываем задачу к текущему пользователю
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    days_until_deadline = calculate_days_until_deadline(new_task.deadline_at)
    task_dict = {
        **new_task.__dict__,
        "is_urgent": is_urgent,
        "days_until_deadline": days_until_deadline
    }
    
    return TaskResponse(**task_dict)


@router.put("/task/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Полное обновление задачи
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Проверка прав доступа - исправлено: убрали .value
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой задаче"
        )
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Пересчитываем квадрант при изменении важных полей
    fields_affecting_quadrant = ["is_important", "deadline_at", "completed"]
    if any(field in update_data for field in fields_affecting_quadrant):
        is_urgent, quadrant = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
        task.quadrant = quadrant
    
    await db.commit()
    await db.refresh(task)
    
    is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    task_dict = {
        **task.__dict__,
        "is_urgent": is_urgent,
        "days_until_deadline": days_until_deadline
    }
    
    return TaskResponse(**task_dict)


@router.patch("/task/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Отметить задачу как выполненную
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Проверка прав доступа - исправлено: убрали .value
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой задаче"
        )
    
    task.completed = True
    task.completed_at = datetime.now()
    
    # При завершении задачи тоже пересчитываем квадрант
    is_urgent, quadrant = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
    task.quadrant = quadrant
    
    await db.commit()
    await db.refresh(task)
    
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    task_dict = {
        **task.__dict__,
        "is_urgent": is_urgent,
        "days_until_deadline": days_until_deadline
    }
    
    return TaskResponse(**task_dict)


@router.delete("/task/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Удаление задачи
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Проверка прав доступа - исправлено: убрали .value
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой задаче"
        )
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "Задача успешно удалена", "id": task.id, "title": task.title}