from fastapi import FastAPI, HTTPException, status, Response, Depends
from pydantic import BaseModel
from app.api.dependencies import check_permissions, get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.dao.base import BaseDAO
from app.dao.users import UserDAO
from app.models.users import User
from app.schemas.user import UserCreate, UserRead
from app.dao.auth import RoleDAO, ElementDAO, RuleDAO

app = FastAPI(title="My Auth Project")

@app.post("/register", response_model=UserRead)
async def register_user(user_data: UserCreate):
    # 1. Проверяем, есть ли такой email (обязательно await!)
    existing_user = await UserDAO.find_one_or_none(email=user_data.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Пользователь с таким email уже существует"
        )

    # 2. Хешируем пароль
    hashed_password = get_password_hash(user_data.password)

    # 3. Добавляем в базу
    await UserDAO.add(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    user = await UserDAO.find_one_or_none(email=user_data.email) # Получаем только что созданного пользователя (у него уже будет id)

    # Возвращаем данные. response_model сама отфильтрует лишнее.
    return user


@app.post("/login")
async def login_user(response: Response, user_data: UserCreate): # Используем UserCreate для валидации входа
    
    user = await UserDAO.find_one_or_none(email=user_data.email)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ваш аккаунт деактивирован. Обратитесь к админу."
        )
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Если все ок, создаем токен
    access_token = create_access_token({"sub": str(user.id)}) # "sub" - это стандартное поле для идентификатора субъекта (пользователя)

    response.set_cookie(key="users_access_token", value=access_token, httponly=True) # Сохраняем токен в куки (только для HTTP, не доступно через JS)
    return {"access_token": access_token, "message": "Успешный вход!"} # Возвращаем токен в теле ответа (на всякий случай)

@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    # Благодаря Depends, этот код не выполнится, если токен плохой.
    # FastAPI сам выкинет 401 ошибку.
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name
    }

@app.post("/logout")
async def logout_user(response: Response):
    # Мы не можем физически удалить куку из браузера с сервера,
    # но мы можем приказать браузеру стереть её значение и поставить срок годности в прошлом.
    response.delete_cookie("users_access_token")
    return {"message": "Вы успешно вышли из системы"}


@app.post("/me/delete")
async def delete_current_user(
    response: Response, 
    current_user: User = Depends(get_current_user)
):
    # 1. Меняем статус на "неактивен"
    await UserDAO.update(filter_id=current_user.id, is_active=False)
    
    # 2. Удаляем куку (logout)
    response.delete_cookie("users_access_token")
    
    return {"message": "Ваш аккаунт деактивирован"}


@app.post("/setup-auth")
@app.post("/setup-auth")
async def setup_auth():
    # 1. Список элементов, которые нам нужны
    target_elements = ["users", "items"]
    for name in target_elements:
        existing = await ElementDAO.find_one_or_none(name=name)
        if not existing:
            await ElementDAO.add(name=name)
            print(f"Элемент {name} создан")

    # 2. Список ролей
    target_roles = ["Admin", "User", "Manager"]
    for name in target_roles:
        existing = await RoleDAO.find_one_or_none(name=name)
        if not existing:
            await RoleDAO.add(name=name)
            print(f"Роль {name} создана")

    try:
        await RuleDAO.add(role_id=1, element_id=1, can_read_all=True, can_update_all=True, can_delete_all=True)
        await RuleDAO.add(role_id=2, element_id=1, can_read=True, can_update=True)
        await RuleDAO.add(role_id=2, element_id=2, can_read=True)
    except Exception as e:
        print("Правила уже были настроены или произошла ошибка при добавлении")

    return {"message": "Инициализация завершена (повторы пропущены)"}

@app.get("/admin/all-users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    await check_permissions(current_user, "users", "can_read_all")
    
    return await UserDAO.find_all()

@app.delete("/admin/delete-user/{target_user_id}")
async def admin_delete_user(
    target_user_id: int, 
    current_user: User = Depends(get_current_user)
):
    await check_permissions(current_user, "users", "can_delete_all")
    
    await UserDAO.update(filter_id=target_user_id, is_active=False)
    return {"message": f"Пользователь {target_user_id} деактивирован администратором"}

class RuleUpdate(BaseModel):
    can_read_all: bool | None = None
    can_update_all: bool | None = None
    can_delete_all: bool | None = None

@app.patch("/admin/rules/{rule_id}")
async def update_rule(
    rule_id: int, 
    rule_data: RuleUpdate, 
    current_user: User = Depends(get_current_user)
):
    if current_user.role_id != 1: 
        raise HTTPException(status_code=403, detail="Только админ управляет правами")
    
    await RuleDAO.update(filter_id=rule_id, **rule_data.model_dump(exclude_unset=True))
    return {"message": "Права обновлены"}

@app.get("/items")
async def get_mock_items(current_user: User = Depends(get_current_user)):
    await check_permissions(current_user, "items", "can_read")
    
    return [
        {"id": 1, "name": "Mock Item A", "price": 100},
        {"id": 2, "name": "Mock Item B", "price": 200}
    ]