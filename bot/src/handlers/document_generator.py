import asyncio
import logging
from typing import Optional

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)


class DocumentGenerationHandler(BaseTaskHandler):
    def __init__(self, api_base_url: str, api_key: Optional[str] = None, concurrency: int = 3):
        super().__init__(api_base_url, api_key)
        self._semaphore = asyncio.Semaphore(concurrency)

    async def process_pending(self):
        try:
            docs = await self._fetch_pending()
            if not docs:
                return 0

            logger.info(f"Documentos pendientes: {len(docs)}")
            async with asyncio.TaskGroup() as tg:
                for doc in docs:
                    tg.create_task(self._process_with_semaphore(doc))
            return len(docs)
        except Exception as e:
            logger.error(f"Error procesando documentos: {e}")
            return 0

    async def _fetch_pending(self):
        try:
            response = await self.api_get("/documents", params={"limit": 10})
            if response.status_code == 200:
                data = response.json()
                return [d for d in data.get("documents", []) if d.get("status") == "pending"]
        except Exception as e:
            logger.warning(f"Error fetching pending documents: {e}")
        return []

    async def _process_with_semaphore(self, doc: dict):
        async with self._semaphore:
            await self._generate(doc)

    async def _generate(self, doc: dict):
        doc_id = doc.get("id")
        logger.info(f"Generando documento: {doc_id}")
        try:
            response = await self.api_post(f"/documents/{doc_id}/generate")
            if response.status_code == 200:
                logger.info(f"Documento {doc_id} generado exitosamente")
            else:
                logger.error(f"Error generando documento {doc_id}: {response.text}")
        except Exception as e:
            logger.error(f"Error en documento {doc_id}: {e}")
