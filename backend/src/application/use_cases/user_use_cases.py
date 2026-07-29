from typing import Optional, List
from datetime import datetime

from ...domain.entities.user import User
from ...domain.value_objects.common import Email, UserRole
from ...domain.repositories.user_repository import UserRepository
from ..dtos.user_dtos import UserCreateDTO, UserUpdateDTO, UserResponseDTO, UserListDTO


class UserUseCases:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def create_user(self, dto: UserCreateDTO) -> UserResponseDTO:
        now = datetime.utcnow().isoformat()
        user = User(
            username=dto.username,
            email=Email(dto.email),
            full_name=dto.full_name,
            role=UserRole(dto.role),
            phone=dto.phone,
            created_at=now,
            updated_at=now,
        )
        created = await self._user_repo.create(user)
        return self._to_response(created)

    async def update_user(self, user_id: str, dto: UserUpdateDTO) -> Optional[UserResponseDTO]:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return None
        if dto.full_name is not None:
            user.full_name = dto.full_name
        if dto.email is not None:
            user.email = Email(dto.email)
        if dto.phone is not None:
            user.phone = dto.phone
        if dto.is_active is not None:
            user.is_active = dto.is_active
        if dto.role is not None:
            user.role = UserRole(dto.role)
        user.updated_at = datetime.utcnow().isoformat()
        updated = await self._user_repo.update(user)
        return self._to_response(updated)

    async def delete_user(self, user_id: str) -> bool:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return False
        await self._user_repo.delete(user_id)
        return True

    async def get_user(self, user_id: str) -> Optional[UserResponseDTO]:
        user = await self._user_repo.get_by_id(user_id)
        return self._to_response(user) if user else None

    async def list_users(self, skip: int = 0, limit: int = 100) -> UserListDTO:
        users = await self._user_repo.list_all(skip=skip, limit=limit)
        total = len(users)
        return UserListDTO(
            users=[self._to_response(u) for u in users],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    def _to_response(user: User) -> UserResponseDTO:
        return UserResponseDTO(
            id=user.id,
            username=user.username,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, 'value') else str(user.role),
            is_active=user.is_active,
            phone=user.phone,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
