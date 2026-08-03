import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class BaseTaskHandler:
    def __init__(self, api_base_url: str, api_key: Optional[str] = None):
        self._api_base_url = api_base_url
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._http = httpx.AsyncClient(
            base_url=api_base_url,
            headers=headers,
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=10.0),
        )

    async def close(self):
        await self._http.aclose()

    async def api_get(self, path: str, **kwargs):
        return await self._http.get(path, **kwargs)

    async def api_post(self, path: str, **kwargs):
        return await self._http.post(path, **kwargs)
