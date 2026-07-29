from typing import Optional, List
from datetime import datetime

from ...domain.entities.inspection import Inspection
from ...domain.entities.inspection_item import InspectionItem
from ...domain.entities.inspection_image import InspectionImage
from ...domain.value_objects.common import InspectionStatus
from ...domain.repositories.inspection_repository import (
    InspectionRepository, InspectionItemRepository, InspectionImageRepository,
)
from ..dtos.inspection_dtos import (
    InspectionCreateDTO, InspectionUpdateDTO, InspectionResponseDTO, InspectionListDTO,
    InspectionItemCreateDTO, InspectionItemUpdateDTO, InspectionItemResponseDTO,
    InspectionImageUploadDTO, InspectionImageResponseDTO, InspectionImageReorderDTO,
)


class InspectionUseCases:
    def __init__(
        self,
        inspection_repo: InspectionRepository,
        item_repo: InspectionItemRepository,
        image_repo: InspectionImageRepository,
    ):
        self._inspection_repo = inspection_repo
        self._item_repo = item_repo
        self._image_repo = image_repo

    async def create_inspection(self, dto: InspectionCreateDTO) -> InspectionResponseDTO:
        now = datetime.utcnow().isoformat()
        inspection = Inspection(
            vehicle_id=dto.vehicle_id,
            inspector_id=dto.inspector_id,
            title=dto.title,
            description=dto.description,
            location=dto.location,
            notes=dto.notes,
            mileage_at_inspection=dto.mileage_at_inspection,
            scheduled_date=dto.scheduled_date,
            client_id=dto.client_id,
            tags=dto.tags,
            created_at=now,
            updated_at=now,
        )
        created = await self._inspection_repo.create(inspection)
        return await self._build_response(created)

    async def update_inspection(self, inspection_id: str, dto: InspectionUpdateDTO) -> Optional[InspectionResponseDTO]:
        inspection = await self._inspection_repo.get_by_id(inspection_id)
        if not inspection:
            return None

        if dto.title is not None:
            inspection.title = dto.title
        if dto.description is not None:
            inspection.description = dto.description
        if dto.location is not None:
            inspection.location = dto.location
        if dto.notes is not None:
            inspection.notes = dto.notes
        if dto.mileage_at_inspection is not None:
            inspection.mileage_at_inspection = dto.mileage_at_inspection
        if dto.scheduled_date is not None:
            inspection.scheduled_date = dto.scheduled_date
        if dto.client_id is not None:
            inspection.client_id = dto.client_id
        if dto.tags is not None:
            inspection.tags = dto.tags
        if dto.status == "completed":
            inspection.complete()
        elif dto.status == "cancelled":
            inspection.cancel()
        elif dto.status is not None:
            inspection.status = InspectionStatus(dto.status)
        inspection.updated_at = datetime.utcnow().isoformat()

        updated = await self._inspection_repo.update(inspection)
        return await self._build_response(updated)

    async def delete_inspection(self, inspection_id: str) -> bool:
        inspection = await self._inspection_repo.get_by_id(inspection_id)
        if not inspection:
            return False
        await self._inspection_repo.delete(inspection_id)
        return True

    async def get_inspection(self, inspection_id: str) -> Optional[InspectionResponseDTO]:
        inspection = await self._inspection_repo.get_by_id(inspection_id)
        return await self._build_response(inspection) if inspection else None

    async def list_inspections(self, skip: int = 0, limit: int = 100) -> InspectionListDTO:
        inspections = await self._inspection_repo.list_all(skip=skip, limit=limit)
        total = await self._inspection_repo.count()
        items = []
        for inv in inspections:
            items.append(await self._build_response(inv))
        return InspectionListDTO(inspections=items, total=total, skip=skip, limit=limit)

    async def complete_inspection(self, inspection_id: str) -> Optional[InspectionResponseDTO]:
        inspection = await self._inspection_repo.get_by_id(inspection_id)
        if not inspection:
            return None
        inspection.complete()
        inspection.updated_at = datetime.utcnow().isoformat()
        updated = await self._inspection_repo.update(inspection)
        return await self._build_response(updated)

    async def add_item(self, dto: InspectionItemCreateDTO) -> InspectionItemResponseDTO:
        now = datetime.utcnow().isoformat()
        item = InspectionItem(
            inspection_id=dto.inspection_id,
            name=dto.name,
            category=dto.category,
            observation=dto.observation,
            score=dto.score,
            is_pass=dto.is_pass,
            position=dto.position,
            created_at=now,
            updated_at=now,
        )
        if dto.score is not None:
            item.set_score(dto.score)
        created = await self._item_repo.create(item)
        return self._item_to_response(created)

    async def update_item(self, item_id: str, dto: InspectionItemUpdateDTO) -> Optional[InspectionItemResponseDTO]:
        item = await self._item_repo.get_by_id(item_id)
        if not item:
            return None
        if dto.name is not None:
            item.name = dto.name
        if dto.category is not None:
            item.category = dto.category
        if dto.observation is not None:
            item.observation = dto.observation
        if dto.score is not None:
            item.set_score(dto.score)
        if dto.is_pass is not None:
            item.is_pass = dto.is_pass
            item.status = "approved" if dto.is_pass else "rejected"
        if dto.position is not None:
            item.position = dto.position
        if dto.status is not None:
            item.status = dto.status
        item.updated_at = datetime.utcnow().isoformat()
        updated = await self._item_repo.update(item)
        return self._item_to_response(updated)

    async def delete_item(self, item_id: str) -> bool:
        item = await self._item_repo.get_by_id(item_id)
        if not item:
            return False
        await self._item_repo.delete(item_id)
        return True

    async def list_items(self, inspection_id: str) -> List[InspectionItemResponseDTO]:
        items = await self._item_repo.list_by_inspection(inspection_id)
        return [self._item_to_response(it) for it in items]

    async def upload_image(
        self, dto: InspectionImageUploadDTO, filename: str, file_path: str, file_size: int, mime_type: str
    ) -> InspectionImageResponseDTO:
        now = datetime.utcnow().isoformat()
        image = InspectionImage(
            inspection_id=dto.inspection_id,
            item_id=dto.item_id,
            filename=filename,
            original_name=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            caption=dto.caption,
            is_cover=dto.is_cover,
            sort_order=dto.sort_order,
            created_at=now,
            updated_at=now,
        )
        created = await self._image_repo.create(image)
        return self._image_to_response(created)

    async def delete_image(self, image_id: str) -> bool:
        image = await self._image_repo.get_by_id(image_id)
        if not image:
            return False
        await self._image_repo.delete(image_id)
        return True

    async def list_images(self, inspection_id: str) -> List[InspectionImageResponseDTO]:
        images = await self._image_repo.list_by_inspection(inspection_id)
        return [self._image_to_response(img) for img in images]

    async def reorder_images(self, dto: InspectionImageReorderDTO) -> None:
        await self._image_repo.reorder(dto.image_ids)

    async def _build_response(self, inspection: Inspection) -> InspectionResponseDTO:
        items = await self._item_repo.list_by_inspection(inspection.id)
        images = await self._image_repo.list_by_inspection(inspection.id)
        return InspectionResponseDTO(
            id=inspection.id,
            vehicle_id=inspection.vehicle_id,
            inspector_id=inspection.inspector_id,
            status=inspection.status.value if hasattr(inspection.status, 'value') else str(inspection.status),
            title=inspection.title,
            description=inspection.description,
            location=inspection.location,
            notes=inspection.notes,
            mileage_at_inspection=inspection.mileage_at_inspection,
            scheduled_date=inspection.scheduled_date,
            completed_date=inspection.completed_date,
            client_id=inspection.client_id,
            tags=inspection.tags,
            items_count=len(items),
            images_count=len(images),
            created_at=inspection.created_at,
            updated_at=inspection.updated_at,
        )

    @staticmethod
    def _item_to_response(item: InspectionItem) -> InspectionItemResponseDTO:
        return InspectionItemResponseDTO(
            id=item.id,
            inspection_id=item.inspection_id,
            name=item.name,
            category=item.category,
            status=item.status,
            observation=item.observation,
            score=item.score,
            is_pass=item.is_pass,
            position=item.position,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _image_to_response(image: InspectionImage) -> InspectionImageResponseDTO:
        return InspectionImageResponseDTO(
            id=image.id,
            inspection_id=image.inspection_id,
            item_id=image.item_id,
            filename=image.filename,
            original_name=image.original_name,
            file_url=f"/api/files/{image.filename}",
            file_size=image.file_size,
            mime_type=image.mime_type,
            width=image.width,
            height=image.height,
            caption=image.caption,
            is_cover=image.is_cover,
            sort_order=image.sort_order,
            created_at=image.created_at,
        )
