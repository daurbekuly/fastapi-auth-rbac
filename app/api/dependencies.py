from fastapi import Request, HTTPException, status, Depends
import jwt
from datetime import datetime, timezone
from app.core.config import settings
from app.dao.users import UserDAO
from app.dao.auth import RoleDAO, ElementDAO, RuleDAO
from app.models.users import User

def get_token(request: Request):
    token = request.cookies.get("users_access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен не найден")
    return token

async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен")

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ID пользователя не найден")
    
    user = await UserDAO.find_one_or_none(id=int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    
    return user

async def check_permissions(user: User, element_name: str, permission_type: str):
    element = await ElementDAO.find_one_or_none(name=element_name)
    if not element:
        raise HTTPException(status_code=500, detail="Элемент системы не найден")

    rule = await RuleDAO.find_one_or_none(role_id=user.role_id, element_id=element.id)
    
    if not rule:
        raise HTTPException(status_code=403, detail="Доступ запрещен (нет правил)")

    has_permission = getattr(rule, permission_type, False)
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Недостаточно прав для этого действия")
    
    return True