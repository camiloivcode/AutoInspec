from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import User
from ....domain.value_objects.common import Email, UserRole
from ....domain.repositories.user_repository import UserRepository
from ..models import UserModel


class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            username=user.username,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, 'value') else str(user.role),
            is_active=user.is_active,
            phone=user.phone,
        )
        self._session.add(model)
        await self._session.flush()
        return user

    async def update(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        if model:
            model.full_name = user.full_name
            model.email = str(user.email)
            model.role = user.role.value if hasattr(user.role, 'value') else str(user.role)
            model.is_active = user.is_active
            model.phone = user.phone
            await self._session.flush()
        return user

    async def delete(self, user_id: str) -> None:
        model = await self._session.get(UserModel, user_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        model = await self._session.get(UserModel, user_id)
        return self._to_domain(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_role(self, role: str) -> List[User]:
        stmt = select(UserModel).where(UserModel.role == role)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(UserModel).offset(skip).limit(limit).order_by(UserModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=Email(model.email),
            full_name=model.full_name,
            role=UserRole(model.role),
            is_active=model.is_active,
            phone=model.phone,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )
