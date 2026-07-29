from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.document import Document


class DocumentRepository(ABC):
    @abstractmethod
    async def create(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def update(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        pass

    @abstractmethod
    async def list_by_inspection(self, inspection_id: str) -> List[Document]:
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Document]:
        pass
