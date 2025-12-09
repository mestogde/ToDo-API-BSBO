# models/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database import Base
import enum


class UserRole(enum.Enum):
    """Перечисление ролей пользователей"""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True
    )
    
    nickname = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    hashed_password = Column(
        String(255),
        nullable=False
    )
    
    # Меняем SQLEnum на String для совместимости с Supabase
    role = Column(
        String(10),  # Вместо SQLEnum(UserRole)
        nullable=False,
        default=UserRole.USER.value  # Используем .value для строки
    )
    
    # Связь с задачами
    tasks = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname='{self.nickname}', role='{self.role}')>"