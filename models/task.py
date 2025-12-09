# models/task.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_important = Column(Boolean, nullable=False, default=False)
    deadline_at = Column(DateTime(timezone=True), nullable=True)
    quadrant = Column(String(2), nullable=False)
    completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Внешний ключ для связи с пользователем
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),  # При удалении пользователя удаляются его задачи
        nullable=False,
        index=True
    )
    
    # Связь с пользователем
    owner = relationship(
        "User",
        back_populates="tasks"
    )
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', quadrant='{self.quadrant}', user_id={self.user_id})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_important": self.is_important,
            "quadrant": self.quadrant,
            "completed": self.completed,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "deadline_at": self.deadline_at,
            "user_id": self.user_id
        }