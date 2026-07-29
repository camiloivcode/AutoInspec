from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..dependencies import get_session, get_template_use_cases
from ...application.use_cases.template_use_cases import TemplateUseCases
from ...application.dtos.template_dtos import TemplateCreateDTO, TemplateUpdateDTO, TemplateResponseDTO, TemplateListDTO

router = APIRouter(prefix="/api/templates", tags=["Templates"])


@router.post("", response_model=TemplateResponseDTO, status_code=201)
async def create_template(
    dto: TemplateCreateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_template_use_cases(session)
    return await use_cases.create_template(dto)


@router.get("", response_model=TemplateListDTO)
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_template_use_cases(session)
    return await use_cases.list_templates(skip=skip, limit=limit)


@router.get("/category/{category}", response_model=List[TemplateResponseDTO])
async def list_by_category(
    category: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_template_use_cases(session)
    return await use_cases.list_by_category(category)


@router.get("/{template_id}", response_model=TemplateResponseDTO)
async def get_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_template_use_cases(session)
    result = await use_cases.get_template(template_id)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.put("/{template_id}", response_model=TemplateResponseDTO)
async def update_template(
    template_id: str,
    dto: TemplateUpdateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_template_use_cases(session)
    result = await use_cases.update_template(template_id, dto)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_template_use_cases(session)
    deleted = await use_cases.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
