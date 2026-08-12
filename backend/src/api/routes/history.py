import os
import json
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["History"])

OUTPUT_DIR = "/data/output"
HISTORY_FILE = "/data/output/history.json"


def _load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_history(records: list):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def save_history_record(driver_name: str, plate: str, filename: str, file_size: int):
    records = _load_history()
    records.insert(0, {
        "id": str(uuid.uuid4()),
        "driver_name": driver_name,
        "plate": plate,
        "filename": filename,
        "file_size": file_size,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _save_history(records)


@router.get("/history")
async def list_history() -> list:
    return _load_history()


@router.get("/history/download/{filename:path}")
async def download_history_file(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(filepath, filename=filename)


@router.delete("/history/{record_id}")
async def delete_history_record(record_id: str):
    records = _load_history()
    updated = [r for r in records if r["id"] != record_id]
    if len(updated) == len(records):
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    _save_history(updated)
    return {"ok": True}
