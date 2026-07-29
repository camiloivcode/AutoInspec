from typing import Optional, List
from datetime import datetime

from ...domain.entities.template import Template
from ...domain.repositories.template_repository import TemplateRepository
from ..dtos.template_dtos import TemplateCreateDTO, TemplateUpdateDTO, TemplateResponseDTO, TemplateListDTO


class TemplateUseCases:
    def __init__(self, template_repo: TemplateRepository):
        self._template_repo = template_repo

    async def create_template(self, dto: TemplateCreateDTO) -> TemplateResponseDTO:
        now = datetime.utcnow().isoformat()
        template = Template(
            name=dto.name,
            description=dto.description,
            category=dto.category,
            content=dto.content,
            variables=dto.variables,
            created_at=now,
            updated_at=now,
        )
        created = await self._template_repo.create(template)
        return self._to_response(created)

    async def update_template(self, template_id: str, dto: TemplateUpdateDTO) -> Optional[TemplateResponseDTO]:
        template = await self._template_repo.get_by_id(template_id)
        if not template:
            return None

        if dto.name is not None:
            template.name = dto.name
        if dto.description is not None:
            template.description = dto.description
        if dto.category is not None:
            template.category = dto.category
        if dto.content is not None:
            template.content = dto.content
        if dto.variables is not None:
            template.variables = dto.variables
        if dto.is_active is not None:
            template.is_active = dto.is_active
        if dto.version is not None:
            template.version = dto.version
        template.updated_at = datetime.utcnow().isoformat()

        updated = await self._template_repo.update(template)
        return self._to_response(updated)

    async def delete_template(self, template_id: str) -> bool:
        template = await self._template_repo.get_by_id(template_id)
        if not template:
            return False
        await self._template_repo.delete(template_id)
        return True

    async def get_template(self, template_id: str) -> Optional[TemplateResponseDTO]:
        template = await self._template_repo.get_by_id(template_id)
        return self._to_response(template) if template else None

    async def list_templates(self, skip: int = 0, limit: int = 100) -> TemplateListDTO:
        templates = await self._template_repo.list_all(skip=skip, limit=limit)
        total = len(templates)
        return TemplateListDTO(
            templates=[self._to_response(t) for t in templates],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def list_by_category(self, category: str) -> List[TemplateResponseDTO]:
        templates = await self._template_repo.list_by_category(category)
        return [self._to_response(t) for t in templates]

    @staticmethod
    def _to_response(template: Template) -> TemplateResponseDTO:
        return TemplateResponseDTO(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            content=template.content,
            variables=template.variables,
            is_active=template.is_active,
            version=template.version,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
