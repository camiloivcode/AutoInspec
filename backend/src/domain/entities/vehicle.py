from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import uuid4

from ..value_objects.common import PlateNumber


@dataclass
class Vehicle:
    brand: str
    model: str
    year: int
    plate: PlateNumber
    vin: Optional[str] = None
    color: Optional[str] = None
    engine_number: Optional[str] = None
    fuel_type: Optional[str] = None
    mileage: Optional[int] = None
    client_id: Optional[str] = None
    notes: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.year < 1900 or self.year > date.today().year + 1:
            raise ValueError(f"Invalid year: {self.year}")

    @property
    def full_name(self) -> str:
        return f"{self.brand} {self.model} ({self.year})"

    @property
    def display_name(self) -> str:
        return f"{self.plate} - {self.full_name}"
