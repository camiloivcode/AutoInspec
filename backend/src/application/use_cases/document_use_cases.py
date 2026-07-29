from typing import Optional, List
from datetime import datetime

from ...domain.entities.document import Document
from ...domain.value_objects.common import DocumentType, DocumentStatus
from ...domain.repositories.document_repository import DocumentRepository
from ...domain.repositories.inspection_repository import InspectionRepository
from ...domain.repositories.template_repository import TemplateRepository
from ...domain.services.document_generator import DocumentGeneratorService
from ..dtos.document_dtos import DocumentCreateDTO, DocumentResponseDTO, DocumentListDTO


class DocumentUseCases:
    def __init__(
        self,
        document_repo: DocumentRepository,
        inspection_repo: InspectionRepository,
        template_repo: TemplateRepository,
        doc_generator: DocumentGeneratorService,
    ):
        self._document_repo = document_repo
        self._inspection_repo = inspection_repo
        self._template_repo = template_repo
        self._doc_generator = doc_generator

    async def create_document(self, dto: DocumentCreateDTO) -> DocumentResponseDTO:
        now = datetime.utcnow().isoformat()
        doc = Document(
            inspection_id=dto.inspection_id,
            template_id=dto.template_id,
            doc_type=DocumentType(dto.doc_type),
            title=dto.title or f"Document-{now[:10]}",
            created_at=now,
            updated_at=now,
        )
        created = await self._document_repo.create(doc)
        return self._to_response(created)

    async def generate_document(self, document_id: str) -> Optional[DocumentResponseDTO]:
        doc = await self._document_repo.get_by_id(document_id)
        if not doc:
            return None

        inspection = await self._inspection_repo.get_by_id(doc.inspection_id)
        template = await self._template_repo.get_by_id(doc.template_id)
        if not inspection or not template:
            if doc:
                doc.mark_error("Inspection or template not found")
                await self._document_repo.update(doc)
            return None

        variables = {
            "inspection_id": inspection.id,
            "inspection_title": inspection.title or "",
            "inspection_date": inspection.scheduled_date or inspection.created_at or "",
            "inspection_location": inspection.location or "",
            "inspection_notes": inspection.notes or "",
            "vehicle_id": inspection.vehicle_id,
            "inspector_id": inspection.inspector_id,
            "client_id": inspection.client_id or "",
            "generated_at": datetime.utcnow().isoformat(),
            **template.variables,
        }

        output_path = f"/tmp/documents/{doc.id}.{'docx' if doc.doc_type == DocumentType.WORD else 'pdf'}"
        try:
            if doc.doc_type == DocumentType.WORD:
                file_path = await self._doc_generator.generate_docx(template.content, variables, output_path)
            else:
                file_path = await self._doc_generator.generate_pdf(template.content, variables, output_path)

            import os
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            doc.mark_generated(file_path, file_size)
        except Exception as e:
            doc.mark_error(str(e))

        doc.updated_at = datetime.utcnow().isoformat()
        updated = await self._document_repo.update(doc)
        return self._to_response(updated)

    async def delete_document(self, document_id: str) -> bool:
        doc = await self._document_repo.get_by_id(document_id)
        if not doc:
            return False
        import os
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        await self._document_repo.delete(document_id)
        return True

    async def get_document(self, document_id: str) -> Optional[DocumentResponseDTO]:
        doc = await self._document_repo.get_by_id(document_id)
        return self._to_response(doc) if doc else None

    async def list_by_inspection(self, inspection_id: str) -> List[DocumentResponseDTO]:
        docs = await self._document_repo.list_by_inspection(inspection_id)
        return [self._to_response(d) for d in docs]

    async def list_all(self, skip: int = 0, limit: int = 100) -> DocumentListDTO:
        docs = await self._document_repo.list_all(skip=skip, limit=limit)
        total = len(docs)
        return DocumentListDTO(
            documents=[self._to_response(d) for d in docs],
            total=total,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    def _to_response(doc: Document) -> DocumentResponseDTO:
        return DocumentResponseDTO(
            id=doc.id,
            inspection_id=doc.inspection_id,
            template_id=doc.template_id,
            doc_type=doc.doc_type.value if hasattr(doc.doc_type, 'value') else str(doc.doc_type),
            status=doc.status.value if hasattr(doc.status, 'value') else str(doc.status),
            title=doc.title,
            file_url=f"/api/files/{doc.file_path.split('/')[-1]}" if doc.file_path else None,
            file_size=doc.file_size,
            generation_notes=doc.generation_notes,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
