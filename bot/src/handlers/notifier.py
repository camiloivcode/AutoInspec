import asyncio
import logging
from typing import Optional

from .base import BaseTaskHandler

logger = logging.getLogger(__name__)


class NotifierHandler(BaseTaskHandler):

    async def send_whatsapp(self, to: str, message: str) -> bool:
        logger.info(f"[WhatsApp] Para: {to} — {message[:80]}...")
        await asyncio.sleep(0.1)
        return True

    async def notify_inspection_complete(self, inspection_id: str, client_phone: Optional[str] = None, driver_name: str = ""):
        if not client_phone:
            logger.info(f"Inspección {inspection_id} completada (sin teléfono para notificar)")
            return True
        message = f"✅ Inspección vehicular completada - {driver_name}. Ya puede descargar su documento."
        return await self.send_whatsapp(client_phone, message)

    async def notify_document_ready(self, document_id: str, client_phone: Optional[str] = None, driver_name: str = ""):
        if not client_phone:
            logger.info(f"Documento {document_id} listo (sin teléfono para notificar)")
            return True
        message = f"📄 Su documento de inspección {driver_name} ya está disponible para descargar."
        return await self.send_whatsapp(client_phone, message)
