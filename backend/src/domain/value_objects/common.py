from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional, List


class InspectionStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    WORD = "word"
    PDF = "pdf"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    GENERATED = "generated"
    ERROR = "error"


class UserRole(str, Enum):
    ADMIN = "admin"
    INSPECTOR = "inspector"
    CLIENT = "client"


@dataclass(frozen=True)
class PlateNumber:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Plate number cannot be empty")

    def __str__(self) -> str:
        return self.value.upper()


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if "@" not in self.value:
            raise ValueError(f"Invalid email: {self.value}")

    def __str__(self) -> str:
        return self.value.lower()


@dataclass(frozen=True)
class PhoneNumber:
    value: str
    country_code: str = "AR"

    def __str__(self) -> str:
        return f"+{self.country_code} {self.value}"


@dataclass(frozen=True)
class Address:
    street: str
    number: str
    city: str
    province: str
    postal_code: str
    country: str = "Argentina"

    def __str__(self) -> str:
        return f"{self.street} {self.number}, {self.city}, {self.province}"


@dataclass(frozen=True)
class DateRange:
    start: date
    end: Optional[date] = None

    def contains(self, d: date) -> bool:
        if self.end:
            return self.start <= d <= self.end
        return d >= self.start

    def __post_init__(self):
        if self.end and self.end < self.start:
            raise ValueError("End date must be after start date")


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "ARS"

    def __str__(self) -> str:
        return f"${self.amount:,.2f} {self.currency}"


@dataclass(frozen=True)
class Percentage:
    value: float

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError("Percentage must be between 0 and 100")

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.1f}%"


@dataclass(frozen=True)
class Dimension:
    length: float
    width: float
    height: float
    unit: str = "cm"

    def __str__(self) -> str:
        return f"{self.length}x{self.width}x{self.height} {self.unit}"


@dataclass(frozen=True)
class Weight:
    value: float
    unit: str = "kg"

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"
