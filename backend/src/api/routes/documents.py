from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..dependencies import get_session, get_document_use_cases
from ...application.use_cases.document_use_cases import DocumentUseCases
from ...application.dtos.document_dtos import DocumentCreateDTO, DocumentResponseDTO, DocumentListDTO

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponseDTO, status_code=201)
async def create_document(
    dto: DocumentCreateDTO,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_document_use_cases(session)
    return await use_cases.create_document(dto)


@router.get("", response_model=DocumentListDTO)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_document_use_cases(session)
    return await use_cases.list_all(skip=skip, limit=limit)


@router.get("/by-inspection/{inspection_id}", response_model=List[DocumentResponseDTO])
async def list_documents_by_inspection(
    inspection_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_document_use_cases(session)
    return await use_cases.list_by_inspection(inspection_id)


@router.get("/{document_id}", response_model=DocumentResponseDTO)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_document_use_cases(session)
    result = await use_cases.get_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@router.post("/{document_id}/generate", response_model=DocumentResponseDTO)
async def generate_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_document_use_cases(session)
    result = await use_cases.generate_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
):
    use_cases = get_document_use_cases(session)
    deleted = await use_cases.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
