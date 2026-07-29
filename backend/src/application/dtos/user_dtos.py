from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class UserCreateDTO:
    username: str
    email: str
    full_name: str
    password: str
    role: str = "inspector"
    phone: Optional[str] = None


@dataclass
class UserUpdateDTO:
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


@dataclass
class UserResponseDTO:
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class UserListDTO:
    users: List[UserResponseDTO]
    total: int
    skip: int = 0
    limit: int = 100
