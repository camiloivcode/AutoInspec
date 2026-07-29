from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.vehicle import Vehicle
from ..value_objects.common import PlateNumber


class VehicleRepository(ABC):
    @abstractmethod
    async def create(self, vehicle: Vehicle) -> Vehicle:
        pass

    @abstractmethod
    async def update(self, vehicle: Vehicle) -> Vehicle:
        pass

    @abstractmethod
    async def delete(self, vehicle_id: str) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        pass

    @abstractmethod
    async def get_by_plate(self, plate: PlateNumber) -> Optional[Vehicle]:
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        pass

    @abstractmethod
    async def search(self, query: str) -> List[Vehicle]:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass
