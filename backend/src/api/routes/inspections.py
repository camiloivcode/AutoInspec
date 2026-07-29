from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..dependencies import get_session, get_inspection_use_cases, get_file_storage
from ...application.use_cases.inspection_use_cases import InspectionUseCases
from ...application.dtos.inspection_dtos import (
    InspectionCreateDTO, InspectionUpdateDTO, InspectionResponseDTO, InspectionListDTO,
    InspectionItemCreateDTO, InspectionItemUpdateDTO, InspectionItemResponseDTO,
    InspectionImageUploadDTO, InspectionImageResponseDTO, InspectionImageReorderDTO,
)
from ...infrastructure.storage import LocalFileStorage

router = APIRouter(prefix="/api/inspections", tags=["Inspections"])


@router.post("", response_model=InspectionResponseDTO, status_code=201)
async def create_inspection(
    dto: InspectionCreateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    return await use_cases.create_inspection(dto)


@router.get("", response_model=InspectionListDTO)
async def list_inspections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    return await use_cases.list_inspections(skip=skip, limit=limit)


@router.get("/{inspection_id}", response_model=InspectionResponseDTO)
async def get_inspection(
    inspection_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    result = await use_cases.get_inspection(inspection_id)
    if not result:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return result


@router.put("/{inspection_id}", response_model=InspectionResponseDTO)
async def update_inspection(
    inspection_id: str,
    dto: InspectionUpdateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    result = await use_cases.update_inspection(inspection_id, dto)
    if not result:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return result


@router.delete("/{inspection_id}", status_code=204)
async def delete_inspection(
    inspection_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    deleted = await use_cases.delete_inspection(inspection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inspection not found")


@router.post("/{inspection_id}/complete", response_model=InspectionResponseDTO)
async def complete_inspection(
    inspection_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    result = await use_cases.complete_inspection(inspection_id)
    if not result:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return result


@router.get("/{inspection_id}/items", response_model=List[InspectionItemResponseDTO])
async def list_items(
    inspection_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    return await use_cases.list_items(inspection_id)


@router.post("/{inspection_id}/items", response_model=InspectionItemResponseDTO, status_code=201)
async def create_item(
    inspection_id: str,
    dto: InspectionItemCreateDTO,
    session: AsyncSession = Depends(get_session),
):
    dto.inspection_id = inspection_id
    use_cases = get_inspection_use_cases(session)
    return await use_cases.add_item(dto)


@router.put("/{inspection_id}/items/{item_id}", response_model=InspectionItemResponseDTO)
async def update_item(
    inspection_id: str,
    item_id: str,
    dto: InspectionItemUpdateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    result = await use_cases.update_item(item_id, dto)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.delete("/{inspection_id}/items/{item_id}", status_code=204)
async def delete_item(
    inspection_id: str,
    item_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    deleted = await use_cases.delete_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")


@router.get("/{inspection_id}/images", response_model=List[InspectionImageResponseDTO])
async def list_images(
    inspection_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    return await use_cases.list_images(inspection_id)


@router.post("/{inspection_id}/images", response_model=InspectionImageResponseDTO, status_code=201)
async def upload_image(
    inspection_id: str,
    file: UploadFile = File(...),
    item_id: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    is_cover: bool = Form(False),
    sort_order: int = Form(0),
    session: AsyncSession = Depends(get_session),
    storage: LocalFileStorage = Depends(get_file_storage),
):
    content = await file.read()
    file_path = await storage.save(content, file.filename, subdir=f"inspections/{inspection_id}")

    dto = InspectionImageUploadDTO(
        inspection_id=inspection_id,
        item_id=item_id,
        caption=caption,
        is_cover=is_cover,
        sort_order=sort_order,
    )
    use_cases = get_inspection_use_cases(session)
    return await use_cases.upload_image(
        dto, file.filename, file_path, len(content), file.content_type or "image/jpeg"
    )


@router.delete("/{inspection_id}/images/{image_id}", status_code=204)
async def delete_image(
    inspection_id: str,
    image_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    deleted = await use_cases.delete_image(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")


@router.post("/{inspection_id}/images/reorder", status_code=204)
async def reorder_images(
    inspection_id: str,
    dto: InspectionImageReorderDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_inspection_use_cases(session)
    await use_cases.reorder_images(dto)
