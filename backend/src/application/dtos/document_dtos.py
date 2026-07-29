from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class DocumentCreateDTO:
    inspection_id: str
    template_id: str
    doc_type: str = "pdf"
    title: str = ""


@dataclass
class DocumentResponseDTO:
    id: str
    inspection_id: str
    template_id: str
    doc_type: str
    status: str
    title: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    generation_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class DocumentListDTO:
    documents: List[DocumentResponseDTO]
    total: int
    skip: int = 0
    limit: int = 100
