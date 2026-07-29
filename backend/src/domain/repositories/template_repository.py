from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.template import Template


class TemplateRepository(ABC):
    @abstractmethod
    async def create(self, template: Template) -> Template:
        pass

    @abstractmethod
    async def update(self, template: Template) -> Template:
        pass

    @abstractmethod
    async def delete(self, template_id: str) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, template_id: str) -> Optional[Template]:
        pass

    @abstractmethod
    async def list_by_category(self, category: str) -> List[Template]:
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Template]:
        pass
