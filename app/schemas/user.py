from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Базовая схема с общими полями
class UserBase(BaseModel):
    email: EmailStr  # Специальный тип, который проверит, есть ли @ и точка
    full_name: Optional[str] = None

# Схема для регистрации (то, что присылает клиент)
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Пароль минимум 8 символов")

# Схема для ответа (то, что мы отдаем клиенту)
class UserRead(UserBase):
    id: int
    is_active: bool

    # Это КРИТИЧЕСКИ важно для работы с SQLAlchemy
    class Config:
        from_attributes = True