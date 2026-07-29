from dataclasses import dataclass, field
from typing import Optional, List
from uuid import uuid4

from ..value_objects.common import UserRole, Email


@dataclass
class User:
    username: str
    email: Email
    full_name: str
    role: UserRole = UserRole.INSPECTOR
    is_active: bool = True
    phone: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Inspector(User):
    license_number: Optional[str] = None
    specializations: List[str] = field(default_factory=list)
    inspection_count: int = 0

    def __post_init__(self):
        self.role = UserRole.INSPECTOR


@dataclass
class Client(User):
    company: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    vehicles_count: int = 0

    def __post_init__(self):
        self.role = UserRole.CLIENT
