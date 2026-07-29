from abc import ABC, abstractmethod
from typing import Dict, Any


class DocumentGeneratorService(ABC):
    @abstractmethod
    async def generate_docx(self, template_content: str, variables: Dict[str, Any], output_path: str) -> str:
        pass

    @abstractmethod
    async def generate_pdf(self, template_content: str, variables: Dict[str, Any], output_path: str) -> str:
        pass

    @abstractmethod
    async def get_preview(self, template_content: str, variables: Dict[str, Any]) -> str:
        pass
