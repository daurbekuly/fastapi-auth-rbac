from sqlalchemy import select, insert
from app.core.database import async_session_maker
from sqlalchemy import update

class BaseDAO:
    model = None

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add(cls, **data):
        async with async_session_maker() as session:
            query = insert(cls.model).values(**data)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def update(cls, filter_id, **data):
        async with async_session_maker() as session:
            query = update(cls.model).where(cls.model.id == filter_id).values(**data)
            await session.execute(query)
            await session.commit()    