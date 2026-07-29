from dataclasses import dataclass, field
from typing import Optional, Dict
from uuid import uuid4


@dataclass
class Template:
    name: str
    description: Optional[str] = None
    category: str = "general"
    content: str = ""
    variables: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    version: str = "1.0"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def variable_list(self) -> list:
        return list(self.variables.keys())
