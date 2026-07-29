from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.vehicle import Vehicle
from ....domain.value_objects.common import PlateNumber
from ....domain.repositories.vehicle_repository import VehicleRepository
from ..models import VehicleModel


class SQLVehicleRepository(VehicleRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, vehicle: Vehicle) -> Vehicle:
        model = VehicleModel(
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
        )
        self._session.add(model)
        await self._session.flush()
        return vehicle

    async def update(self, vehicle: Vehicle) -> Vehicle:
        model = await self._session.get(VehicleModel, vehicle.id)
        if model:
            model.brand = vehicle.brand
            model.model = vehicle.model
            model.year = vehicle.year
            model.plate = str(vehicle.plate)
            model.vin = vehicle.vin
            model.color = vehicle.color
            model.engine_number = vehicle.engine_number
            model.fuel_type = vehicle.fuel_type
            model.mileage = vehicle.mileage
            model.client_id = vehicle.client_id
            model.notes = vehicle.notes
            await self._session.flush()
        return vehicle

    async def delete(self, vehicle_id: str) -> None:
        model = await self._session.get(VehicleModel, vehicle_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        model = await self._session.get(VehicleModel, vehicle_id)
        return self._to_domain(model) if model else None

    async def get_by_plate(self, plate: PlateNumber) -> Optional[Vehicle]:
        stmt = select(VehicleModel).where(VehicleModel.plate == str(plate))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        stmt = select(VehicleModel).offset(skip).limit(limit).order_by(VehicleModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def search(self, query: str) -> List[Vehicle]:
        pattern = f"%{query}%"
        stmt = select(VehicleModel).where(
            or_(
                VehicleModel.plate.ilike(pattern),
                VehicleModel.brand.ilike(pattern),
                VehicleModel.model.ilike(pattern),
                VehicleModel.vin.ilike(pattern),
            )
        ).limit(20)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count(self) -> int:
        stmt = select(func.count(VehicleModel.id))
        result = await self._session.execute(stmt)
        return result.scalar()

    @staticmethod
    def _to_domain(model: VehicleModel) -> Vehicle:
        return Vehicle(
            id=model.id,
            brand=model.brand,
            model=model.model,
            year=model.year,
            plate=PlateNumber(model.plate),
            vin=model.vin,
            color=model.color,
            engine_number=model.engine_number,
            fuel_type=model.fuel_type,
            mileage=model.mileage,
            client_id=model.client_id,
            notes=model.notes,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )
