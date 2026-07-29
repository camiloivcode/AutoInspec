from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class InspectionCreateDTO:
    vehicle_id: str
    inspector_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    mileage_at_inspection: Optional[int] = None
    scheduled_date: Optional[str] = None
    client_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class InspectionUpdateDTO:
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    mileage_at_inspection: Optional[int] = None
    scheduled_date: Optional[str] = None
    client_id: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


@dataclass
class InspectionResponseDTO:
    id: str
    vehicle_id: str
    inspector_id: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    mileage_at_inspection: Optional[int] = None
    scheduled_date: Optional[str] = None
    completed_date: Optional[str] = None
    client_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    items_count: int = 0
    images_count: int = 0
    documents_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class InspectionListDTO:
    inspections: List[InspectionResponseDTO]
    total: int
    skip: int = 0
    limit: int = 100


@dataclass
class InspectionItemCreateDTO:
    inspection_id: str
    name: str
    category: str
    observation: Optional[str] = None
    score: Optional[int] = None
    is_pass: Optional[bool] = None
    position: int = 0


@dataclass
class InspectionItemUpdateDTO:
    name: Optional[str] = None
    category: Optional[str] = None
    observation: Optional[str] = None
    score: Optional[int] = None
    is_pass: Optional[bool] = None
    position: Optional[int] = None
    status: Optional[str] = None


@dataclass
class InspectionItemResponseDTO:
    id: str
    inspection_id: str
    name: str
    category: str
    status: str
    observation: Optional[str] = None
    score: Optional[int] = None
    is_pass: Optional[bool] = None
    position: int = 0
    images_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class InspectionImageUploadDTO:
    inspection_id: str
    item_id: Optional[str] = None
    caption: Optional[str] = None
    is_cover: bool = False
    sort_order: int = 0


@dataclass
class InspectionImageResponseDTO:
    id: str
    inspection_id: str
    filename: str
    original_name: str
    item_id: Optional[str] = None
    file_url: str = ""
    file_size: int = 0
    mime_type: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    caption: Optional[str] = None
    is_cover: bool = False
    sort_order: int = 0
    created_at: Optional[str] = None


@dataclass
class InspectionImageReorderDTO:
    image_ids: List[str]
