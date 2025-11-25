from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Название задачи",
        examples=["Изучить FastAPI"]
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Описание задачи",
        examples=["Пройти tutorial и сделать проект"]
    )
    is_important: bool = Field(
        ...,
        description="Важность задачи",
        examples=[True]
    )
    is_urgent: bool = Field(
        ...,
        description="Срочность задачи",
        examples=[False]
    )

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="Новое название задачи"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Новое описание"
    )
    is_important: Optional[bool] = Field(
        None,
        description="Новая важность"
    )
    is_urgent: Optional[bool] = Field(
        None,
        description="Новая срочность"
    )
    completed: Optional[bool] = Field(
        None,
        description="Статус выполнения"
    )

class TaskResponse(TaskBase):
    id: int = Field(
        ...,
        description="Уникальный идентификатор задачи",
        examples=[1]
    )
    quadrant: str = Field(
        ...,
        description="Квадрант матрицы Эйзенхауэра",
        examples=["Q1"]
    )
    completed: bool = Field(
        default=False,
        description="Статус выполнения задачи"
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания задачи"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Дата и время завершения задачи"
    )
    
    @validator('quadrant')
    def validate_quadrant(cls, v):
        if v not in ['Q1', 'Q2', 'Q3', 'Q4']:
            raise ValueError('Квадрант должен быть Q1, Q2, Q3 или Q4')
        return v
    
    class Config:
        from_attributes = True