from typing import Optional, List
from datetime import datetime

from ...domain.entities.vehicle import Vehicle
from ...domain.value_objects.common import PlateNumber
from ...domain.repositories.vehicle_repository import VehicleRepository
from ..dtos.vehicle_dtos import VehicleCreateDTO, VehicleUpdateDTO, VehicleResponseDTO, VehicleListDTO


class VehicleUseCases:
    def __init__(self, vehicle_repo: VehicleRepository):
        self._vehicle_repo = vehicle_repo

    async def create_vehicle(self, dto: VehicleCreateDTO) -> VehicleResponseDTO:
        plate = PlateNumber(dto.plate)
        now = datetime.utcnow().isoformat()
        vehicle = Vehicle(
            brand=dto.brand,
            model=dto.model,
            year=dto.year,
            plate=plate,
            vin=dto.vin,
            color=dto.color,
            engine_number=dto.engine_number,
            fuel_type=dto.fuel_type,
            mileage=dto.mileage,
            client_id=dto.client_id,
            notes=dto.notes,
            created_at=now,
            updated_at=now,
        )
        created = await self._vehicle_repo.create(vehicle)
        return self._to_response(created)

    async def update_vehicle(self, vehicle_id: str, dto: VehicleUpdateDTO) -> Optional[VehicleResponseDTO]:
        vehicle = await self._vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            return None

        if dto.brand is not None:
            vehicle.brand = dto.brand
        if dto.model is not None:
            vehicle.model = dto.model
        if dto.year is not None:
            vehicle.year = dto.year
        if dto.plate is not None:
            vehicle.plate = PlateNumber(dto.plate)
        if dto.vin is not None:
            vehicle.vin = dto.vin
        if dto.color is not None:
            vehicle.color = dto.color
        if dto.engine_number is not None:
            vehicle.engine_number = dto.engine_number
        if dto.fuel_type is not None:
            vehicle.fuel_type = dto.fuel_type
        if dto.mileage is not None:
            vehicle.mileage = dto.mileage
        if dto.client_id is not None:
            vehicle.client_id = dto.client_id
        if dto.notes is not None:
            vehicle.notes = dto.notes
        vehicle.updated_at = datetime.utcnow().isoformat()

        updated = await self._vehicle_repo.update(vehicle)
        return self._to_response(updated)

    async def delete_vehicle(self, vehicle_id: str) -> bool:
        vehicle = await self._vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            return False
        await self._vehicle_repo.delete(vehicle_id)
        return True

    async def get_vehicle(self, vehicle_id: str) -> Optional[VehicleResponseDTO]:
        vehicle = await self._vehicle_repo.get_by_id(vehicle_id)
        return self._to_response(vehicle) if vehicle else None

    async def list_vehicles(self, skip: int = 0, limit: int = 100) -> VehicleListDTO:
        vehicles = await self._vehicle_repo.list_all(skip=skip, limit=limit)
        total = await self._vehicle_repo.count()
        return VehicleListDTO(
            vehicles=[self._to_response(v) for v in vehicles],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def search_vehicles(self, query: str) -> List[VehicleResponseDTO]:
        vehicles = await self._vehicle_repo.search(query)
        return [self._to_response(v) for v in vehicles]

    @staticmethod
    def _to_response(vehicle: Vehicle) -> VehicleResponseDTO:
        return VehicleResponseDTO(
            id=vehicle.id,
            brand=vehicle.brand,
            model=vehicle.model,
            year=vehicle.year,
            plate=str(vehicle.plate),
            vin=vehicle.vin,
            color=vehicle.color,
            engine_number=vehicle.engine_number,
            fuel_type=vehicle.fuel_type,
            mileage=vehicle.mileage,
            client_id=vehicle.client_id,
            notes=vehicle.notes,
            full_name=vehicle.full_name,
            display_name=vehicle.display_name,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
        )
