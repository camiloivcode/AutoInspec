from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4


@dataclass
class InspectionImage:
    inspection_id: str
    item_id: Optional[str] = None
    filename: str = ""
    original_name: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = "image/jpeg"
    width: Optional[int] = None
    height: Optional[int] = None
    caption: Optional[str] = None
    is_cover: bool = False
    sort_order: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
