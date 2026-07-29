from abc import ABC, abstractmethod
from typing import Optional
import os
import shutil
import aiofiles
from uuid import uuid4


class FileStorage(ABC):
    @abstractmethod
    async def save(self, content: bytes, filename: str, subdir: str = "") -> str:
        pass

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        pass

    @abstractmethod
    async def get_path(self, filename: str, subdir: str = "") -> Optional[str]:
        pass


class LocalFileStorage(FileStorage):
    def __init__(self, base_path: str = "/data"):
        self._base_path = base_path

    async def save(self, content: bytes, filename: str, subdir: str = "") -> str:
        dir_path = os.path.join(self._base_path, subdir) if subdir else self._base_path
        os.makedirs(dir_path, exist_ok=True)

        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid4()}{ext}"
        file_path = os.path.join(dir_path, unique_name)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        return file_path

    async def delete(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    async def get_path(self, filename: str, subdir: str = "") -> Optional[str]:
        dir_path = os.path.join(self._base_path, subdir) if subdir else self._base_path
        candidate = os.path.join(dir_path, filename)
        return candidate if os.path.exists(candidate) else None
