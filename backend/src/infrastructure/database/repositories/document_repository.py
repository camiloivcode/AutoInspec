from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.document import Document
from ....domain.value_objects.common import DocumentType, DocumentStatus
from ....domain.repositories.document_repository import DocumentRepository
from ..models import DocumentModel


class SQLDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, document: Document) -> Document:
        model = DocumentModel(
            id=document.id,
            inspection_id=document.inspection_id,
            template_id=document.template_id,
            doc_type=document.doc_type.value if hasattr(document.doc_type, 'value') else str(document.doc_type),
            status=document.status.value if hasattr(document.status, 'value') else str(document.status),
            title=document.title,
            file_path=document.file_path,
            file_size=document.file_size,
            generation_notes=document.generation_notes,
        )
        self._session.add(model)
        await self._session.flush()
        return document

    async def update(self, document: Document) -> Document:
        model = await self._session.get(DocumentModel, document.id)
        if model:
            model.status = document.status.value if hasattr(document.status, 'value') else str(document.status)
            model.title = document.title
            model.file_path = document.file_path
            model.file_size = document.file_size
            model.generation_notes = document.generation_notes
            await self._session.flush()
        return document

    async def delete(self, document_id: str) -> None:
        model = await self._session.get(DocumentModel, document_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        model = await self._session.get(DocumentModel, document_id)
        return self._to_domain(model) if model else None

    async def list_by_inspection(self, inspection_id: str) -> List[Document]:
        stmt = select(DocumentModel).where(
            DocumentModel.inspection_id == inspection_id
        ).order_by(DocumentModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        stmt = select(DocumentModel).offset(skip).limit(limit).order_by(DocumentModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            inspection_id=model.inspection_id,
            template_id=model.template_id,
            doc_type=DocumentType(model.doc_type),
            status=DocumentStatus(model.status),
            title=model.title,
            file_path=model.file_path,
            file_size=model.file_size,
            generation_notes=model.generation_notes,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )
