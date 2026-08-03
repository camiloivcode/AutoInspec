import asyncio
import logging
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from .config import BotSettings
from .services.redis_client import RedisClient
from .handlers.document_generator import DocumentGenerationHandler
from .handlers.inspection_handler import InspectionHandler
from .handlers.notifier import NotifierHandler

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
        self._redis = RedisClient(self.settings.redis_url)
        self._doc_handler = DocumentGenerationHandler(
            self.settings.api_base_url,
            self.settings.api_key,
            concurrency=3,
        )
        self._insp_handler = InspectionHandler(
            self.settings.api_base_url,
            self.settings.api_key,
            concurrency=5,
        )
        self._notifier = NotifierHandler(
            self.settings.api_base_url,
            self.settings.api_key,
        )
        self._running = False

    async def start(self):
        self._running = True
        logger.info(f"Bot iniciado. API: {self.settings.api_base_url}")
        logger.info(f"Redis: {self.settings.redis_url}")

        await self._redis.connect()
        await self._check_api_health()

        tasks = [
            asyncio.create_task(self._polling_loop()),
            asyncio.create_task(self._redis.subscribe("task:generate", self._on_generate_task)),
        ]
        logger.info("Bot listo — polling + escuchando tareas Redis")

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()

    async def stop(self):
        self._running = False
        await self._redis.disconnect()
        await self._doc_handler.close()
        await self._insp_handler.close()
        await self._notifier.close()
        logger.info("Bot detenido.")

    async def _check_api_health(self) -> bool:
        try:
            response = await self._doc_handler.api_get("/health")
            if response.status_code == 200:
                logger.info(f"Conexión con API establecida: {response.json()}")
                return True
            logger.warning(f"API respondió con status {response.status_code}")
            return False
        except Exception as e:
            logger.warning(f"No se pudo conectar con la API: {e}")
            return False

    async def _polling_loop(self):
        backoff = 1
        while self._running:
            try:
                total = 0
                total += await self._doc_handler.process_pending()
                total += await self._insp_handler.process_pending()
                backoff = 1 if total > 0 else min(backoff * 2, 60)
            except Exception as e:
                logger.error(f"Error en ciclo de polling: {e}")
                backoff = min(backoff * 2, 60)
            await asyncio.sleep(backoff)

    async def _on_generate_task(self, data: dict):
        task_type = data.get("type", "")
        task_id = data.get("id", "")
        logger.info(f"Tarea recibida: {task_type} [{task_id}]")

        locked = await self._redis.try_lock(f"task:{task_type}:{task_id}", ttl=300)
        if not locked:
            logger.debug(f"Tarea {task_id} ya en proceso, saltando")
            return

        try:
            if task_type == "generate_document":
                doc = {"id": task_id}
                await self._doc_handler._generate(doc)
            elif task_type == "notify_whatsapp":
                await self._notifier.notify_inspection_complete(
                    task_id,
                    data.get("phone"),
                    data.get("driver_name", ""),
                )
            else:
                logger.warning(f"Tipo de tarea desconocido: {task_type}")
        except Exception as e:
            logger.error(f"Error ejecutando tarea {task_id}: {e}")
        finally:
            await self._redis.release_lock(f"task:{task_type}:{task_id}")


async def main():
    bot = InspectionBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
