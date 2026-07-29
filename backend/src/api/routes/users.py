from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..dependencies import get_session, get_user_use_cases
from ...application.use_cases.user_use_cases import UserUseCases
from ...application.dtos.user_dtos import UserCreateDTO, UserUpdateDTO, UserResponseDTO, UserListDTO

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("", response_model=UserResponseDTO, status_code=201)
async def create_user(
    dto: UserCreateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_user_use_cases(session)
    return await use_cases.create_user(dto)


@router.get("", response_model=UserListDTO)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_user_use_cases(session)
    return await use_cases.list_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_user_use_cases(session)
    result = await use_cases.get_user(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.put("/{user_id}", response_model=UserResponseDTO)
async def update_user(
    user_id: str,
    dto: UserUpdateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_user_use_cases(session)
    result = await use_cases.update_user(user_id, dto)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_user_use_cases(session)
    deleted = await use_cases.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
