from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.template import Template
from ....domain.repositories.template_repository import TemplateRepository
from ..models import TemplateModel


class SQLTemplateRepository(TemplateRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, template: Template) -> Template:
        model = TemplateModel(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            content=template.content,
            variables=template.variables,
            is_active=template.is_active,
            version=template.version,
        )
        self._session.add(model)
        await self._session.flush()
        return template

    async def update(self, template: Template) -> Template:
        model = await self._session.get(TemplateModel, template.id)
        if model:
            model.name = template.name
            model.description = template.description
            model.category = template.category
            model.content = template.content
            model.variables = template.variables
            model.is_active = template.is_active
            model.version = template.version
            await self._session.flush()
        return template

    async def delete(self, template_id: str) -> None:
        model = await self._session.get(TemplateModel, template_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def get_by_id(self, template_id: str) -> Optional[Template]:
        model = await self._session.get(TemplateModel, template_id)
        return self._to_domain(model) if model else None

    async def list_by_category(self, category: str) -> List[Template]:
        stmt = select(TemplateModel).where(TemplateModel.category == category)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Template]:
        stmt = select(TemplateModel).offset(skip).limit(limit).order_by(TemplateModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    @staticmethod
    def _to_domain(model: TemplateModel) -> Template:
        return Template(
            id=model.id,
            name=model.name,
            description=model.description,
            category=model.category,
            content=model.content,
            variables=model.variables or {},
            is_active=model.is_active,
            version=model.version,
            created_at=model.created_at.isoformat() if model.created_at else None,
            updated_at=model.updated_at.isoformat() if model.updated_at else None,
        )
