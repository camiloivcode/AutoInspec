import asyncio
import logging
from typing import Optional

import httpx
from rich.console import Console
from rich.logging import RichHandler

from .config import BotSettings

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("bot")


class InspectionBot:
    def __init__(self, settings: Optional[BotSettings] = None):
        self.settings = settings or BotSettings()
        self._client: Optional[httpx.AsyncClient] = None
        self._running = False

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.settings.api_key:
                headers["Authorization"] = f"Bearer {self.settings.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.settings.api_base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def start(self):
        self._running = True
        logger.info(f"Bot iniciado. API: {self.settings.api_base_url}")
        logger.info("Modo: Escuchando eventos para procesamiento...")

        await self.check_api_health()

        while self._running:
            try:
                await self.process_pending_tasks()
            except Exception as e:
                logger.error(f"Error en ciclo principal: {e}")
            await asyncio.sleep(self.settings.polling_interval_seconds)

    async def stop(self):
        self._running = False
        if self._client:
            await self._client.aclose()
        logger.info("Bot detenido.")

    async def check_api_health(self) -> bool:
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                logger.info(f"Conexión con API establecida: {response.json()}")
                return True
            logger.warning(f"API respondió con status {response.status_code}")
            return False
        except Exception as e:
            logger.warning(f"No se pudo conectar con la API: {e}")
            return False

    async def process_pending_tasks(self):
        tasks_to_process = await self._fetch_pending_documents()
        for task in tasks_to_process:
            await self._process_document_generation(task)

        pending_inspections = await self._fetch_pending_inspections()
        for inspection in pending_inspections:
            await self._process_inspection_completion(inspection)

    async def _fetch_pending_documents(self) -> list:
        try:
            response = await self.client.get("/documents", params={"limit": 10})
            if response.status_code == 200:
                data = response.json()
                return [
                    doc for doc in data.get("documents", [])
                    if doc.get("status") == "pending"
                ]
        except Exception as e:
            logger.debug(f"Error fetching pending documents: {e}")
        return []

    async def _process_document_generation(self, doc: dict):
        doc_id = doc.get("id")
        logger.info(f"Procesando documento pendiente: {doc_id}")
        try:
            response = await self.client.post(f"/documents/{doc_id}/generate")
            if response.status_code == 200:
                logger.info(f"Documento {doc_id} generado exitosamente")
            else:
                logger.error(f"Error generando documento {doc_id}: {response.text}")
        except Exception as e:
            logger.error(f"Error en documento {doc_id}: {e}")

    async def _fetch_pending_inspections(self) -> list:
        try:
            response = await self.client.get("/inspections", params={"limit": 10})
            if response.status_code == 200:
                data = response.json()
                return [
                    inv for inv in data.get("inspections", [])
                    if inv.get("status") == "in_progress"
                ]
        except Exception as e:
            logger.debug(f"Error fetching pending inspections: {e}")
        return []

    async def _process_inspection_completion(self, inspection: dict):
        inv_id = inspection.get("id")
        logger.info(f"Revisando inspección en progreso: {inv_id}")

    async def process_image_ocr(self, image_url: str) -> Optional[dict]:
        logger.info(f"Procesando OCR para imagen: {image_url}")
        await asyncio.sleep(0.1)
        return None

    async def notify_whatsapp(self, to: str, message: str) -> bool:
        logger.info(f"Notificación WhatsApp a {to}: {message[:50]}...")
        await asyncio.sleep(0.1)
        return True

    async def process_batch(self, inspection_ids: list[str]) -> dict:
        results = {"success": 0, "failed": 0, "details": []}
        for inv_id in inspection_ids:
            try:
                response = await self.client.post(f"/inspections/{inv_id}/complete")
                if response.status_code == 200:
                    results["success"] += 1
                    results["details"].append({"id": inv_id, "status": "completed"})
                else:
                    results["failed"] += 1
                    results["details"].append({"id": inv_id, "status": "failed"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"id": inv_id, "error": str(e)})
        return results


async def main():
    bot = InspectionBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
