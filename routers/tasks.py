from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date, time

from database import get_async_session
from models.task import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter()


def calculate_urgency_and_quadrant(deadline_at: Optional[datetime], is_important: bool) -> tuple[bool, str]:
    """Рассчитывает срочность и квадрант на основе дедлайна и важности"""
    if not deadline_at:
        # Если дедлайна нет - считаем не срочным
        is_urgent = False
    else:
        # Рассчитываем разницу в днях между сегодня и дедлайном
        today = date.today()
        deadline_date = deadline_at.date()
        
        # Обрабатываем случай, когда дедлайн уже прошел
        if deadline_date < today:
            is_urgent = True  # Просроченные задачи считаем срочными
        else:
            days_until_deadline = (deadline_date - today).days
            is_urgent = days_until_deadline <= 3
    
    # Определяем квадрант
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
    
    # Возвращаем отрицательное число для просроченных задач
    return (deadline_date - today).days


@router.get("", response_model=List[TaskResponse])
async def get_all_tasks(db: AsyncSession = Depends(get_async_session)) -> List[TaskResponse]:
    """
    Получение всех задач
    
    Returns:
        List[TaskResponse]: Список всех задач
    """
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    
    # Добавляем расчетные поля для ответа
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
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """
    Поиск задач по ключевому слову
    
    - **q**: Ключевое слово для поиска (минимум 2 символа)
    """
    keyword = f"%{q.lower()}%"
    
    # SELECT * FROM tasks
    # WHERE LOWER(title) LIKE '%keyword%'
    # OR LOWER(description) LIKE '%keyword%'
    result = await db.execute(
        select(Task).where(
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
    
    # Добавляем расчетные поля
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
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """
    Фильтрация задач по статусу выполнения
    
    - **status**: Статус задачи ("completed" или "pending")
    """
    if status not in ["completed", "pending"]:
        raise HTTPException(
            status_code=404, 
            detail="Недопустимый статус. Используйте: completed или pending"
        )
    
    is_completed = (status == "completed")
    result = await db.execute(select(Task).where(Task.completed == is_completed))
    tasks = result.scalars().all()
    
    # Добавляем расчетные поля
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
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """
    Фильтрация задач по квадранту
    
    - **quadrant**: Квадрант матрицы Эйзенхауэра ("Q1", "Q2", "Q3", "Q4")
    """
    if quadrant not in ["Q1", "Q2", "Q3", "Q4"]:
        raise HTTPException(
            status_code=400,
            detail="Неверный квадрант. Используйте: Q1, Q2, Q3, Q4"
        )
    
    result = await db.execute(select(Task).where(Task.quadrant == quadrant))
    tasks = result.scalars().all()
    
    # Добавляем расчетные поля
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
    db: AsyncSession = Depends(get_async_session)
) -> List[TaskResponse]:
    """
    Получение задач, срок которых истекает сегодня
    
    Returns:
        List[TaskResponse]: Список задач с дедлайном на сегодня
    """
    # Получаем сегодняшнюю дату (без времени)
    today = date.today()
    
    # Создаем диапазон для сегодняшнего дня (с 00:00 до 23:59)
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    # Ищем задачи с дедлайном в диапазоне сегодняшнего дня
    result = await db.execute(
        select(Task).where(
            Task.deadline_at.between(today_start, today_end),
            Task.completed == False  # Только невыполненные задачи
        )
    )
    tasks = result.scalars().all()
    
    # Добавляем расчетные поля для ответа
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


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """
    Получение задачи по ID
    
    - **task_id**: ID задачи (целое число)
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Добавляем расчетные поля
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
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """
    Создание новой задачи
    
    - **title**: Название задачи (обязательное, 3-100 символов)
    - **description**: Описание задачи (опциональное, до 500 символов)
    - **is_important**: Важная ли задача
    - **is_urgent**: Срочная ли задача
    """
    # Рассчитываем срочность и квадрант
    is_urgent, quadrant = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
    
    new_task = Task(
        title=task.title,
        description=task.description,
        is_important=task.is_important,
        deadline_at=task.deadline_at,
        quadrant=quadrant,
        completed=False
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Добавляем расчетные поля для ответа
    days_until_deadline = calculate_days_until_deadline(new_task.deadline_at)
    task_dict = {
        **new_task.__dict__,
        "is_urgent": is_urgent,
        "days_until_deadline": days_until_deadline
    }
    
    return TaskResponse(**task_dict)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """
    Полное обновление задачи
    
    - **task_id**: ID задачи для обновления
    - **task_update**: Данные для обновления (все поля опциональные)
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Обновляем поля
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # ВСЕГДА пересчитываем квадрант при изменении ЛЮБОГО поля, влияющего на логику
    fields_affecting_quadrant = ["is_important", "deadline_at", "completed"]
    if any(field in update_data for field in fields_affecting_quadrant):
        is_urgent, quadrant = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
        task.quadrant = quadrant
    
    await db.commit()
    await db.refresh(task)
    
    # Добавляем расчетные поля для ответа
    is_urgent, _ = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    task_dict = {
        **task.__dict__,
        "is_urgent": is_urgent,
        "days_until_deadline": days_until_deadline
    }
    
    return TaskResponse(**task_dict)


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> TaskResponse:
    """
    Отметить задачу как выполненную
    
    - **task_id**: ID задачи для отметки как выполненной
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Обновляем статус выполнения
    task.completed = True
    task.completed_at = datetime.now()
    
    # При завершении задачи тоже пересчитываем квадрант
    is_urgent, quadrant = calculate_urgency_and_quadrant(task.deadline_at, task.is_important)
    task.quadrant = quadrant
    
    await db.commit()
    await db.refresh(task)
    
    # Добавляем расчетные поля для ответа
    days_until_deadline = calculate_days_until_deadline(task.deadline_at)
    
    task_dict = {
        **task.__dict__,
        "is_urgent": is_urgent,
        "days_until_deadline": days_until_deadline
    }
    
    return TaskResponse(**task_dict)


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Удаление задачи
    
    - **task_id**: ID задачи для удаления
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    await db.delete(task)
    await db.commit()
    return {"message": "Задача успешно удалена", "id": task.id, "title": task.title}