import asyncio
import logging
from typing import Optional

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)


class InspectionHandler(BaseTaskHandler):
    def __init__(self, api_base_url: str, api_key: Optional[str] = None, concurrency: int = 5):
        super().__init__(api_base_url, api_key)
        self._semaphore = asyncio.Semaphore(concurrency)

    async def process_pending(self):
        try:
            inspections = await self._fetch_pending()
            if not inspections:
                return 0

            logger.info(f"Inspecciones en progreso: {len(inspections)}")
            for inv in inspections:
                await self._process(inv)
            return len(inspections)
        except Exception as e:
            logger.error(f"Error procesando inspecciones: {e}")
            return 0

    async def _fetch_pending(self):
        try:
            response = await self.api_get("/inspections", params={"limit": 10})
            if response.status_code == 200:
                data = response.json()
                return [inv for inv in data.get("inspections", []) if inv.get("status") == "in_progress"]
        except Exception as e:
            logger.warning(f"Error fetching inspections: {e}")
        return []

    async def _process(self, inspection: dict):
        inv_id = inspection.get("id")
        title = inspection.get("title", inv_id)
        try:
            response = await self.api_get(f"/inspections/{inv_id}")
            if response.status_code != 200:
                return
            detail = response.json()
            items = detail.get("items", [])
            if items:
                all_approved = all(i.get("is_pass", False) for i in items)
                if all_approved:
                    logger.info(f"Inspección {inv_id} completa, todos los items aprobados")
        except Exception as e:
            logger.debug(f"Error revisando inspección {inv_id}: {e}")

    async def complete(self, inspection_id: str) -> bool:
        try:
            response = await self.api_post(f"/inspections/{inspection_id}/complete")
            return response.status_code == 200
        except Exception:
            return False
