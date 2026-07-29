from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.inspection import Inspection
from ..entities.inspection_item import InspectionItem
from ..entities.inspection_image import InspectionImage


class InspectionRepository(ABC):
    @abstractmethod
    async def create(self, inspection: Inspection) -> Inspection:
        pass

    @abstractmethod
    async def update(self, inspection: Inspection) -> Inspection:
        pass

    @abstractmethod
    async def delete(self, inspection_id: str) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, inspection_id: str) -> Optional[Inspection]:
        pass

    @abstractmethod
    async def list_by_vehicle(self, vehicle_id: str) -> List[Inspection]:
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Inspection]:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass


class InspectionItemRepository(ABC):
    @abstractmethod
    async def create(self, item: InspectionItem) -> InspectionItem:
        pass

    @abstractmethod
    async def update(self, item: InspectionItem) -> InspectionItem:
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, item_id: str) -> Optional[InspectionItem]:
        pass

    @abstractmethod
    async def list_by_inspection(self, inspection_id: str) -> List[InspectionItem]:
        pass


class InspectionImageRepository(ABC):
    @abstractmethod
    async def create(self, image: InspectionImage) -> InspectionImage:
        pass

    @abstractmethod
    async def update(self, image: InspectionImage) -> InspectionImage:
        pass

    @abstractmethod
    async def delete(self, image_id: str) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, image_id: str) -> Optional[InspectionImage]:
        pass

    @abstractmethod
    async def list_by_inspection(self, inspection_id: str) -> List[InspectionImage]:
        pass

    @abstractmethod
    async def list_by_item(self, item_id: str) -> List[InspectionImage]:
        pass

    @abstractmethod
    async def reorder(self, image_ids: List[str]) -> None:
        pass
