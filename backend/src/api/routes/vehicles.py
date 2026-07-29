from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..dependencies import get_session, get_vehicle_use_cases
from ...application.use_cases.vehicle_use_cases import VehicleUseCases
from ...application.dtos.vehicle_dtos import VehicleCreateDTO, VehicleUpdateDTO, VehicleResponseDTO, VehicleListDTO

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleResponseDTO, status_code=201)
async def create_vehicle(
    dto: VehicleCreateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_vehicle_use_cases(session)
    return await use_cases.create_vehicle(dto)


@router.get("", response_model=VehicleListDTO)
async def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_vehicle_use_cases(session)
    return await use_cases.list_vehicles(skip=skip, limit=limit)


@router.get("/search", response_model=List[VehicleResponseDTO])
async def search_vehicles(
    q: str = Query("", min_length=1),
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_vehicle_use_cases(session)
    return await use_cases.search_vehicles(q)


@router.get("/{vehicle_id}", response_model=VehicleResponseDTO)
async def get_vehicle(
    vehicle_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_vehicle_use_cases(session)
    result = await use_cases.get_vehicle(vehicle_id)
    if not result:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return result


@router.put("/{vehicle_id}", response_model=VehicleResponseDTO)
async def update_vehicle(
    vehicle_id: str,
    dto: VehicleUpdateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_vehicle_use_cases(session)
    result = await use_cases.update_vehicle(vehicle_id, dto)
    if not result:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return result


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(
    vehicle_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_vehicle_use_cases(session)
    deleted = await use_cases.delete_vehicle(vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vehicle not found")
