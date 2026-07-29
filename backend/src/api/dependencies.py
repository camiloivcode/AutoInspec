from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.database.settings import get_session_factory
from ..infrastructure.database.repositories import (
    SQLVehicleRepository, SQLInspectionRepository, SQLInspectionItemRepository,
    SQLInspectionImageRepository, SQLDocumentRepository, SQLTemplateRepository,
    SQLUserRepository,
)
from ..infrastructure.document_generation import WordGeneratorService, PDFGeneratorService
from ..infrastructure.storage import LocalFileStorage
from ..application.use_cases import (
    VehicleUseCases, InspectionUseCases, DocumentUseCases,
    TemplateUseCases, UserUseCases,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


def get_vehicle_use_cases(session: AsyncSession) -> VehicleUseCases:
    repo = SQLVehicleRepository(session)
    return VehicleUseCases(repo)


def get_inspection_use_cases(session: AsyncSession) -> InspectionUseCases:
    inspection_repo = SQLInspectionRepository(session)
    item_repo = SQLInspectionItemRepository(session)
    image_repo = SQLInspectionImageRepository(session)
    return InspectionUseCases(inspection_repo, item_repo, image_repo)


def get_document_use_cases(session: AsyncSession) -> DocumentUseCases:
    doc_repo = SQLDocumentRepository(session)
    inspection_repo = SQLInspectionRepository(session)
    template_repo = SQLTemplateRepository(session)
    word_gen = WordGeneratorService()
    pdf_gen = PDFGeneratorService(word_gen)
    return DocumentUseCases(doc_repo, inspection_repo, template_repo, pdf_gen)


def get_template_use_cases(session: AsyncSession) -> TemplateUseCases:
    repo = SQLTemplateRepository(session)
    return TemplateUseCases(repo)


def get_user_use_cases(session: AsyncSession) -> UserUseCases:
    repo = SQLUserRepository(session)
    return UserUseCases(repo)


def get_file_storage() -> LocalFileStorage:
    return LocalFileStorage(base_path="/data/uploads")
