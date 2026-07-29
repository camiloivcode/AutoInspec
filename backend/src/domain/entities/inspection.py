from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from ..value_objects.common import InspectionStatus


@dataclass
class Inspection:
    vehicle_id: str
    inspector_id: str
    status: InspectionStatus = InspectionStatus.DRAFT
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    mileage_at_inspection: Optional[int] = None
    scheduled_date: Optional[str] = None
    completed_date: Optional[str] = None
    client_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def complete(self) -> None:
        self.status = InspectionStatus.COMPLETED
        self.completed_date = datetime.utcnow().isoformat()

    def cancel(self) -> None:
        self.status = InspectionStatus.CANCELLED

    def add_note(self, note: str) -> None:
        existing = self.notes or ""
        self.notes = f"{existing}\n[{datetime.utcnow().isoformat()}] {note}".strip()
