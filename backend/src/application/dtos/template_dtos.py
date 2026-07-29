from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class TemplateCreateDTO:
    name: str
    description: Optional[str] = None
    category: str = "general"
    content: str = ""
    variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class TemplateUpdateDTO:
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
    version: Optional[str] = None


@dataclass
class TemplateResponseDTO:
    id: str
    name: str
    category: str
    content: str
    variables: Dict[str, str]
    is_active: bool
    version: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class TemplateListDTO:
    templates: List[TemplateResponseDTO]
    total: int
    skip: int = 0
    limit: int = 100
