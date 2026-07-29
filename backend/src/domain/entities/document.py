from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from ..value_objects.common import DocumentType, DocumentStatus


@dataclass
class Document:
    inspection_id: str
    template_id: str
    doc_type: DocumentType = DocumentType.PDF
    status: DocumentStatus = DocumentStatus.PENDING
    title: str = ""
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    generation_notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def mark_generated(self, file_path: str, file_size: int) -> None:
        self.status = DocumentStatus.GENERATED
        self.file_path = file_path
        self.file_size = file_size

    def mark_error(self, error: str) -> None:
        self.status = DocumentStatus.ERROR
        self.generation_notes = error
