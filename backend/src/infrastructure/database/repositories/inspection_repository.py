from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.inspection import Inspection
from ....domain.entities.inspection_item import InspectionItem
from ....domain.entities.inspection_image import InspectionImage
from ....domain.value_objects.common import InspectionStatus
from ....domain.repositories.inspection_repository import (
    InspectionRepository, InspectionItemRepository, InspectionImageRepository,
)
from ..models import InspectionModel, InspectionItemModel, InspectionImageModel


class SQLInspectionRepository(InspectionRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, inspection: Inspection) -> Inspection:
        model = InspectionModel(
            id=inspection.id,
            vehicle_id=inspection.vehicle_id,
            inspector_id=inspection.inspector_id,
            status=inspection.status.value if hasattr(inspection.status, 'value') else str(inspection.status),
            title=inspection.title,
            description=inspection.description,
            location=inspection.location,
            notes=inspection.notes,
            mileage_at_inspection=inspection.mileage_at_inspection,
            client_id=inspection.client_id,
            tags=inspection.tags,
        )
        self._session.add(model)
        await self._session.flush()
        return inspection

    async def update(self, inspection: Inspection) -> Inspection:
        model = await self._session.get(InspectionModel, inspection.id)
        if model:
            model.vehicle_id = inspection.vehicle_id
            model.inspector_id = inspection.inspector_id
            model.status = inspection.status.value if hasattr(inspection.status, 'value') else str(inspection.status)
            model.title = inspection.title
            model.description = inspection.description
            model.location = inspection.location
            model.notes = inspection.notes
            model.mileage_at_inspection = inspection.mileage_at_inspection
            model.scheduled_date = inspection.scheduled_date
            model.completed_date = inspection.completed_date
            model.client_id = inspection.client_id
            model.tags = inspection.tags
            await self._session.flush()
        return inspection

    async def delete(self, inspection_id: str) -> None:
        model = await self._session.get(InspectionModel, inspection_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, inspection_id: str) -> Optional[Inspection]:
        model = await self._session.get(InspectionModel, inspection_id)
        return self._to_domain(model) if model else None

    async def list_by_vehicle(self, vehicle_id: str) -> List[Inspection]:
        stmt = select(InspectionModel).where(
            InspectionModel.vehicle_id == vehicle_id
        ).order_by(InspectionModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Inspection]:
        stmt = select(InspectionModel).offset(skip).limit(limit).order_by(InspectionModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count(self) -> int:
        stmt = select(func.count(InspectionModel.id))
        result = await self._session.execute(stmt)
        return result.scalar()

    @staticmethod
    def _to_domain(model: InspectionModel) -> Inspection:
        return Inspection(
            id=model.id,
            vehicle_id=model.vehicle_id,
            inspector_id=model.inspector_id,
            status=InspectionStatus(model.status),
            title=model.title,
            description=model.description,
            location=model.location,
            notes=model.notes,
            mileage_at_inspection=model.mileage_at_inspection,
            scheduled_date=model.scheduled_date.isoformat() if model.scheduled_date else None,
            completed_date=model.completed_date.isoformat() if model.completed_date else None,
            client_id=model.client_id,
            tags=model.tags or [],
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )


class SQLInspectionItemRepository(InspectionItemRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, item: InspectionItem) -> InspectionItem:
        model = InspectionItemModel(
            id=item.id,
            inspection_id=item.inspection_id,
            name=item.name,
            category=item.category,
            status=item.status,
            observation=item.observation,
            score=item.score,
            is_pass=item.is_pass,
            position=item.position,
        )
        self._session.add(model)
        await self._session.flush()
        return item

    async def update(self, item: InspectionItem) -> InspectionItem:
        model = await self._session.get(InspectionItemModel, item.id)
        if model:
            model.name = item.name
            model.category = item.category
            model.status = item.status
            model.observation = item.observation
            model.score = item.score
            model.is_pass = item.is_pass
            model.position = item.position
            await self._session.flush()
        return item

    async def delete(self, item_id: str) -> None:
        model = await self._session.get(InspectionItemModel, item_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, item_id: str) -> Optional[InspectionItem]:
        model = await self._session.get(InspectionItemModel, item_id)
        return self._to_domain(model) if model else None

    async def list_by_inspection(self, inspection_id: str) -> List[InspectionItem]:
        stmt = select(InspectionItemModel).where(
            InspectionItemModel.inspection_id == inspection_id
        ).order_by(InspectionItemModel.position)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: InspectionItemModel) -> InspectionItem:
        return InspectionItem(
            id=model.id,
            inspection_id=model.inspection_id,
            name=model.name,
            category=model.category,
            status=model.status,
            observation=model.observation,
            score=model.score,
            is_pass=model.is_pass,
            position=model.position,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )


class SQLInspectionImageRepository(InspectionImageRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, image: InspectionImage) -> InspectionImage:
        model = InspectionImageModel(
            id=image.id,
            inspection_id=image.inspection_id,
            item_id=image.item_id,
            filename=image.filename,
            original_name=image.original_name,
            file_path=image.file_path,
            file_size=image.file_size,
            mime_type=image.mime_type,
            width=image.width,
            height=image.height,
            caption=image.caption,
            is_cover=image.is_cover,
            sort_order=image.sort_order,
        )
        self._session.add(model)
        await self._session.flush()
        return image

    async def update(self, image: InspectionImage) -> InspectionImage:
        model = await self._session.get(InspectionImageModel, image.id)
        if model:
            model.item_id = image.item_id
            model.caption = image.caption
            model.is_cover = image.is_cover
            model.sort_order = image.sort_order
            await self._session.flush()
        return image

    async def delete(self, image_id: str) -> None:
        model = await self._session.get(InspectionImageModel, image_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, image_id: str) -> Optional[InspectionImage]:
        model = await self._session.get(InspectionImageModel, image_id)
        return self._to_domain(model) if model else None

    async def list_by_inspection(self, inspection_id: str) -> List[InspectionImage]:
        stmt = select(InspectionImageModel).where(
            InspectionImageModel.inspection_id == inspection_id
        ).order_by(InspectionImageModel.sort_order)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_item(self, item_id: str) -> List[InspectionImage]:
        stmt = select(InspectionImageModel).where(
            InspectionImageModel.item_id == item_id
        ).order_by(InspectionImageModel.sort_order)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def reorder(self, image_ids: List[str]) -> None:
        for idx, img_id in enumerate(image_ids):
            await self._session.execute(
                update(InspectionImageModel)
                .where(InspectionImageModel.id == img_id)
                .values(sort_order=idx)
            )
        await self._session.flush()

    @staticmethod
    def _to_domain(model: InspectionImageModel) -> InspectionImage:
        return InspectionImage(
            id=model.id,
            inspection_id=model.inspection_id,
            item_id=model.item_id,
            filename=model.filename,
            original_name=model.original_name,
            file_path=model.file_path,
            file_size=model.file_size,
            mime_type=model.mime_type,
            width=model.width,
            height=model.height,
            caption=model.caption,
            is_cover=model.is_cover,
            sort_order=model.sort_order,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )
